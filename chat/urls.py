from django.urls import path

from .views import HomeView, chat_room_view

app_name = 'chat'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('room/<slug:chat_owner_slug>/', chat_room_view, name='chat_room'),
]
