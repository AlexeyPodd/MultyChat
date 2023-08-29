from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView

from account.models import User
from chat.base_views import user_management_list_view
from chat.redis_interface import RedisChatLogInterface


class HomeView(ListView):
    template_name = 'chat/home.html'
    model = User
    context_object_name = 'users'
    extra_context = {'title': 'MultyChats - Home'}


@login_required
def chat_room_view(request, chat_owner_slug):
    chat_owner = get_object_or_404(User.objects.prefetch_related('moderators', 'black_listed_users'),
                                   username_slug=chat_owner_slug)
    moder_username_list = list(chat_owner.moderators.values_list('username', flat=True))
    black_list_usernames = request.user.black_listed_users.values_list('username', flat=True)
    am_banned = request.user.bans.filter(chat_owner=chat_owner, time_end__gt=timezone.now()).exists()

    return render(request,
                  'chat/room.html',
                  {'title': f"Chat - {chat_owner.username}",
                   'chat_owner': chat_owner,
                   'moder_username_list': moder_username_list,
                   'black_list_usernames': black_list_usernames,
                   'last_messages': RedisChatLogInterface.get_chat_log_data(chat_owner.username),
                   'am_banned': am_banned})


@user_management_list_view(
    users_list_filed_name='black_listed_users',
    title="My black list",
    bootstrap_btn_color='btn-warning',
    button_label='Exclude from Black List',
    empty_phrase='Black List is Empty',
)
def black_list_view():
    """View for managing black list, deleting users from it."""
    pass


@user_management_list_view(
    users_list_filed_name='moderators',
    title="My Moderators",
    bootstrap_btn_color='btn-danger',
    button_label='Demote Moderator',
    empty_phrase='You have no moderators',
)
def moderator_list_view():
    """
    View for managing moderator list.
    If moderator is not in chat now - this view would be the only comfortable way to demote him.
     """
    pass
