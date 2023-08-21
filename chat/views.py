from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView

from account.models import User
from chat.redis_interface import RedisChatLogInterface


class HomeView(ListView):
    template_name = 'chat/home.html'
    model = User
    context_object_name = 'users'
    extra_context = {'title': 'MultyChats - Home'}


@login_required
def chat_room_view(request, chat_owner_slug):
    chat_owner = get_object_or_404(User, username_slug=chat_owner_slug)

    return render(request,
                  'chat/room.html',
                  {'title': f"Chat - {chat_owner_slug}",
                   'chat_owner': chat_owner,
                   'last_messages': RedisChatLogInterface.get_chat_log_data(chat_owner_slug)})
