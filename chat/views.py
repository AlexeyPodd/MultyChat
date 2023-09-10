from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F, OuterRef, Prefetch, Exists
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
    model = Ban
    template_name = 'chat/banned_users_list.html'
    context_object_name = 'banned_users'

    def get_queryset(self):
        # # Ban instances for PostgreSQL, for another not possible because of distinct('banned_user')
        # bans_of_users_in_user_chat = self.model.objects.filter(
        #     Q(time_end=None) | Q(time_end__gt=timezone.now()),
        #     chat_owner=self.request.user,
        # ).order_by(F('time_end').desc(nulls_first=True)).distinct('banned_user')

        active_bans = Ban.objects.filter(
            Q(time_end=None) | Q(time_end__gt=timezone.now()),
            banned_user=OuterRef('pk'),
            chat_owner=self.request.user,
        )
        dominant_ban = Ban.objects.filter(
            Q(time_end=None) | Q(time_end__gt=timezone.now()),
            chat_owner=self.request.user,
        ).order_by(F('time_end').desc(nulls_first=True))[:1]
        baned_users_in_user_chat = User.objects.filter(Exists(active_bans)).prefetch_related(
            Prefetch('bans', queryset=dominant_ban, to_attr='dominant_ban')).order_by('username')

        return baned_users_in_user_chat

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context.update({
            'title': 'MultyChat - manage bans',
            'empty_phrase': 'You have no banned users',
        })
        return context


def unban_user_ajax_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not Authenticated'}, status=403)

    banned_username = request.POST.get('bannedUsername')
    owner_username = request.POST.get('chatOwnerUsername')

    print(banned_username, owner_username)

    try:
        banned = User.objects.get(username=banned_username)
        owner = User.objects.get(username=owner_username)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Not Founded', 'model': 'User'}, status=404)

    if not (request.user == owner or request.user in owner.moderators):
        return JsonResponse({'error': 'Permission Denied'}, status=403)

    bans = banned.bans.filter(Q(time_end=None) | Q(time_end__gt=timezone.now()), chat_owner=owner)

    if not bans:
        return JsonResponse({'error': 'Not Founded', 'model': 'Ban'}, status=404)

    if request.user != owner and bans.filter(time_end__isnull=True).exists():
        return JsonResponse({'error': 'Permission Denied'}, status=403)

    bans.delete()
    return JsonResponse({'user_unbanned': banned_username})
