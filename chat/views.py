from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView

from account.models import User


class HomeView(ListView):
    template_name = 'chat/home.html'
    model = User
    context_object_name = 'users'
    extra_context = {'title': 'MultyChats - Home'}


@login_required
def chat_room_view(request, chat_owner_slug):
    chat_owner = get_object_or_404(User, username_slug=chat_owner_slug)
    if not chat_owner.is_running_chat:
        raise Http404

    return render(request, 'chat/room.html', {'title': f"Chat - {chat_owner_slug}",
                                              'chat_owner_slug': chat_owner_slug})
