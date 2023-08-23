from django.urls import path

from .views import HomeView, chat_room_view, black_list_view

app_name = 'chat'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('room/<slug:chat_owner_slug>/', chat_room_view, name='chat_room'),
    path('black_list', black_list_view, name='black_list'),
]
