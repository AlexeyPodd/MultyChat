import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from django.utils import timezone

from account.models import User
from multychats.settings import  GLOBAL_CHANNELS_GROUP_NAME
from .consumer_mixins import ChatMessagingMixin, SystemMessagingMixin


class ChatRoomConsumer(ChatMessagingMixin, SystemMessagingMixin, AsyncWebsocketConsumer):
    """
    Consumer for chat. Handling user's messages and system commands.
    """

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        await self._set_chat_user_parameters()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.channel_layer.group_add(
            GLOBAL_CHANNELS_GROUP_NAME,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        match text_data_json.get('messageType'):
            case "message":
                await self._handle_chat_message(text_data_json)
            case "management":
                await self._handle_management_message(text_data_json)

    async def _set_chat_user_parameters(self):
        chat_owner_slug = self.scope['url_route']['kwargs']['chat_owner_slug']
        chat_owner = await User.objects.aget(username_slug=chat_owner_slug)
        self.chat_owner_username = chat_owner.username
        self.room_group_name = f'chat_{self.chat_owner_username}'
        self._black_list_usernames = await database_sync_to_async(set)(self.scope['user'].black_listed_users.
                                                                       values_list('username', flat=True))
        self._moderator = await database_sync_to_async(
            self.scope['user'].moderating_user_chats.filter(username_slug=chat_owner_slug).exists)()
        self._banned = await database_sync_to_async(self.scope['user'].bans.filter(
            Q(chat_owner=chat_owner) | Q(chat_owner=None),
            Q(time_end__gt=timezone.now()) | Q(time_end=None)).exists)()
