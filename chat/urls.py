from django.urls import path

from .views import HomeView, chat_room_view, black_list_view, moderator_list_view, BannedListView, unban_user_ajax_view, \
    get_chat_banned_info

app_name = 'chat'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('room/<slug:chat_owner_slug>/', chat_room_view, name='chat-room'),
    path('black-list/', black_list_view, name='black-list'),
    path('moderators/', moderator_list_view, name='moder-list'),
    path('banned-users/', BannedListView.as_view(), name='banned-list'),
    path('unban-user/', unban_user_ajax_view, name='ajax-unban-user'),
    path('banned-users-in-other-user-chat/', get_chat_banned_info, name='ajax-banned-list'),
]
