from django.urls import path

from .views import HomeView, chat_room_view, black_list_view, moderator_list_view

app_name = 'chat'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('room/<slug:chat_owner_slug>/', chat_room_view, name='chat_room'),
    path('black-list/', black_list_view, name='black_list'),
    path('moderators/', moderator_list_view, name='moder_list'),
]
