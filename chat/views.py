from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView

from account.models import User
from chat.base_views import user_management_list_view
from chat.redis_interface import RedisChatLogInterface
from multychats.settings import CHAT_USER_STATUSES


class HomeView(ListView):
    template_name = 'chat/home.html'
    model = User
    context_object_name = 'users'
    extra_context = {'title': 'MultyChats - Home'}


@login_required
def chat_room_view(request, chat_owner_slug):
    chat_owner = get_object_or_404(User.objects.prefetch_related('moderators', 'black_listed_users'),
                                   username_slug=chat_owner_slug)
    black_list_usernames = request.user.black_listed_users.values_list('username', flat=True)
    am_moder = request.user.moderating_user_chats.filter(username_slug=chat_owner_slug).exists()
    am_banned = request.user.bans.filter(chat_owner=chat_owner, time_end__gt=timezone.now()).exists()

    return render(request,
                  'chat/room.html',
                  {'title': f"Chat - {chat_owner.username}",
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
                  {'title': "My black list",
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
                  {'title': "My Moderators",
                   'bootstrap_btn_color': 'btn-danger',
                   'button_label': 'Demote Moderator',
                   'empty_phrase': 'You have no moderators',
                   'user_list': managed_user_list})
