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
    chat_owner = get_object_or_404(User.objects.prefetch_related('moderators'), username_slug=chat_owner_slug)
    moder_slug_list = list(chat_owner.moderators.values_list('username_slug', flat=True))

    return render(request,
                  'chat/room.html',
                  {'title': f"Chat - {chat_owner_slug}",
                   'chat_owner': chat_owner,
                   'moder_slug_list': moder_slug_list,
                   'last_messages': RedisChatLogInterface.get_chat_log_data(chat_owner_slug)})


@login_required
def black_list_view(request):
    black_listed_users = request.user.black_listed_users.all()
    return render(request,
                  'chat/black_list.html',
                  {'title': f"My black list",
                   'black_listed_users': black_listed_users})
