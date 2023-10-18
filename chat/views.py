from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView

from account.models import User
from chat.base_views import user_management_list_view
from chat.models import Ban
from chat.redis_interface import RedisChatLogInterface
from multychats.settings import CHAT_USER_STATUSES


class HomeView(ListView):
    template_name = 'chat/home.html'
    model = User
    context_object_name = 'users'
    extra_context = {'title': 'MultyChats - home'}


@login_required
def chat_room_view(request, chat_owner_slug):
    """Represents chat room."""

    chat_owner = get_object_or_404(User.objects.prefetch_related('moderators', 'black_listed_users'),
                                   username_slug=chat_owner_slug)
    black_list_usernames = request.user.black_listed_users.values_list('username', flat=True)
    am_moder = request.user.moderating_user_chats.filter(username_slug=chat_owner_slug).exists()
    am_banned = request.user.bans.filter(Q(time_end__gt=timezone.now()) | Q(time_end=None),
                                         chat_owner=chat_owner).exists()

    return render(request,
                  'chat/room.html',
                  {'title': f"MultyChat - {chat_owner.username} room",
                   'chat_owner': chat_owner,
                   'black_list_usernames': black_list_usernames,
                   'user_statuses': CHAT_USER_STATUSES,
                   'last_messages': RedisChatLogInterface.get_chat_log_data(chat_owner.username),
                   'am_moder': am_moder,
                   'am_banned': am_banned})


@user_management_list_view(users_list_filed_name='black_listed_users')
def black_list_view(request, managed_user_list):
    """View for managing black list, deleting users from it."""
    return render(request,
                  'chat/manage_user_list.html',
                  {'title': "MultyChat - my black list",
                   'bootstrap_btn_color': 'btn-warning',
                   'button_label': 'Exclude from Black List',
                   'empty_phrase': 'Black List is Empty',
                   'user_list': managed_user_list})


@user_management_list_view(users_list_filed_name='moderators')
def moderator_list_view(request, managed_user_list):
    """
    View for managing moderator list.
    If moderator is not in chat now - this view would be the only comfortable way to demote him.
     """
    if request.method == 'POST':
        RedisChatLogInterface.change_user_status(chat_owner_username=request.user.username,
                                                 username=request.POST.get('username'),
                                                 new_status=CHAT_USER_STATUSES[4])
    return render(request,
                  'chat/manage_user_list.html',
                  {'title': "MultyChat - my moderators",
                   'bootstrap_btn_color': 'btn-danger',
                   'button_label': 'Demote Moderator',
                   'empty_phrase': 'You have no moderators',
                   'user_list': managed_user_list})


class BannedListView(LoginRequiredMixin, ListView):
    """View for managing banned users and bans itself"""

    model = Ban
    template_name = 'chat/banned_users_list.html'
    context_object_name = 'bans'

    def get_queryset(self):
        # Ban instances for PostgreSQL, for another not possible because of distinct('banned_user')
        bans_of_users_in_user_chat = self.model.objects.filter(
            Q(time_end=None) | Q(time_end__gt=timezone.now()),
            chat_owner=self.request.user,
        ).order_by('banned_user', F('time_end').desc(nulls_first=True)).distinct('banned_user')

        # # Users, who is banned, with prefetch related the longest term ban
        # active_bans = Ban.objects.filter(
        #     Q(time_end=None) | Q(time_end__gt=timezone.now()),
        #     banned_user=OuterRef('pk'),
        #     chat_owner=self.request.user,
        # )
        # dominant_ban = Ban.objects.filter(
        #     Q(time_end=None) | Q(time_end__gt=timezone.now()),
        #     chat_owner=self.request.user,
        # ).order_by(F('time_end').desc(nulls_first=True))[:1]
        # baned_users_in_user_chat = User.objects.filter(Exists(active_bans)).prefetch_related(
        #     Prefetch('bans', queryset=dominant_ban, to_attr='dominant_ban')).order_by('username')

        return bans_of_users_in_user_chat

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context.update({
            'title': 'MultyChat - manage bans',
            'empty_phrase': 'You have no banned users',
        })
        return context


def unban_user_ajax_view(request):
    """
    View for deleting bans of user in chat. Empty string for chat owner == in all chats (for admins).
    If ban id specified - will be deleted just specified ban, otherwise - all active bans in specified chat for user.
    """

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not Authenticated'}, status=403)

    ban_id = request.POST.get('banId')
    if ban_id:
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission Denied'}, status=403)

        if not ban_id.isdigit():
            return JsonResponse({'error': 'Id was not Integer'}, status=400)

        bans = Ban.objects.filter(id=int(ban_id))
        banned_username = bans[0].banned_user.username if bans else None

    else:
        banned_username = request.POST.get('bannedUsername')
        owner_username = request.POST.get('chatOwnerUsername')

        if not owner_username:
            # unban in all chats can only admin
            if not request.user.is_staff:
                return JsonResponse({'error': 'Permission Denied'}, status=403)
            owner = None
        else:
            try:
                owner = User.objects.get(username=owner_username)
            except ObjectDoesNotExist:
                return JsonResponse({'error': 'Not Founded', 'model': 'User'}, status=404)

        try:
            banned = User.objects.get(username=banned_username)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Not Founded', 'model': 'User'}, status=404)

        # if user does not have privilege to unban in this chat
        if not (request.user.is_staff or owner and request.user == owner or request.user in owner.moderators.all()):
            return JsonResponse({'error': 'Permission Denied'}, status=403)

        bans = banned.bans.filter(Q(time_end=None) | Q(time_end__gt=timezone.now()), chat_owner=owner)

        # if user is moder (not admin or owner) and ban is indefinite
        if not request.user.is_staff and owner and request.user != owner and bans.filter(time_end__isnull=True).exists():
            return JsonResponse({'error': 'Permission Denied'}, status=403)

    if not bans:
        return JsonResponse({'error': 'Not Founded', 'model': 'Ban'}, status=404)

    bans.delete()
    return JsonResponse({'user_unbanned': banned_username})


def get_chat_banned_info_ajax_view(request):
    """
    View for ajax request of banned users in some chat.
    Returns list of data of unique users with latest expire date ban.
    """

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not Authenticated'}, status=403)

    owner_username = request.GET.get('owner')

    try:
        owner = User.objects.get(username=owner_username)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Not Founded', 'model': 'User'}, status=404)

    # Checking permission (admin, owner or moderator)
    if not (request.user.is_staff or request.user == owner or request.user in owner.moderators.all()):
        return JsonResponse({'error': 'Permission Denied'}, status=403)

    bans = Ban.objects.filter(
            Q(time_end=None) | Q(time_end__gt=timezone.now()),
            chat_owner=owner,
        ).order_by('banned_user', F('time_end').desc(nulls_first=True)).distinct('banned_user')

    data = list(bans.values('banned_user__username', 'time_start', 'time_end', 'banned_by__username'))
    return JsonResponse({'data': data})


def get_banned_admin_info_ajax_view(request):
    """
    View for admin of the site, for ajax request of bans.
    Returns list of data of bans, according to request:
    (all or just active - of specific chat, or of specific user, or of specific user in specific chat).
    """

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not Authenticated'}, status=403)

    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission Denied'}, status=403)

    owner_username = request.GET.get('owner')
    banned_username = request.GET.get('user')
    try:
        get_all_bans = bool(int(request.GET.get('all', 0)))
    except ValueError:
        return JsonResponse({'error': 'Non-Numeric Parameter \'all\''}, status=400)

    if not owner_username and not banned_username:
        return JsonResponse({'error': 'No Search Criteria'}, status=400)

    if owner_username:
        try:
            owner = User.objects.get(username=owner_username)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Not Founded', 'model': 'User (chat owner)'}, status=404)

    if banned_username:
        try:
            banned_user = User.objects.get(username=banned_username)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Not Founded', 'model': 'User (banned user)'}, status=404)

    if owner_username and banned_username:
        bans = (Ban.objects.filter(chat_owner=owner, banned_user=banned_user)
                .order_by(F('time_end').desc(nulls_first=True)))
        if not get_all_bans:
            bans = bans.filter(Q(time_end=None) | Q(time_end__gt=timezone.now()))[:1]
    elif owner_username:
        bans = Ban.objects.filter(chat_owner=owner).order_by('banned_user', F('time_end').desc(nulls_first=True))
        if not get_all_bans:
            bans = bans.filter(Q(time_end=None) | Q(time_end__gt=timezone.now())).distinct('banned_user')
    elif banned_username:
        bans = Ban.objects.filter(banned_user=banned_user).order_by('chat_owner', F('time_end').desc(nulls_first=True))
        if not get_all_bans:
            bans = bans.filter(Q(time_end=None) | Q(time_end__gt=timezone.now())).distinct('chat_owner')

    data = list(bans.values('id', 'banned_user__username', 'chat_owner__username',
                            'time_start', 'time_end', 'banned_by__username'))

    return JsonResponse({'data': data})
