import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist

from account.models import User
from . import cache_manager
from chat.redis_interface import RedisChatLogInterface, RedisChatStatusInterface


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_owner_slug = self.scope['url_route']['kwargs']['chat_owner_slug']
        self.room_group_name = f'chat_{self.chat_owner_slug}'

        if self.scope['user'].is_authenticated:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name,
            )

            await self.accept()
        else:
            await self.close()

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

    async def _handle_chat_message(self, text_data_json):
        message = text_data_json.get('message')
        sender_username = text_data_json.get('userUsername')
        sender_slug = text_data_json.get('userUsernameSlug')

        if not await cache_manager.get_or_set_from_db_chat_open_status(self.chat_owner_slug):
            return

        if not message or not sender_username:
            return

        RedisChatLogInterface.log_chat_message(chat_owner_slug=self.chat_owner_slug,
                                               author_username=sender_username,
                                               author_slug=sender_slug,
                                               message=message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chatroom_message',
             'message': message,
             "sender_username": sender_username,
             "sender_slug": sender_slug},
        )

    async def chatroom_message(self, event):
        message = event['message']
        sender_username = event['sender_username']
        sender_slug = event['sender_slug']

        await self.send(text_data=json.dumps({'message': message,
                                              'senderUsername': sender_username,
                                              'senderUsernameSlug': sender_slug,
                                              'messageType': 'chatroom_message'}))

    async def _handle_management_message(self, text_data_json):
        command = text_data_json.get('command')

        match command:
            case "open_chat":
                if (not await cache_manager.get_or_set_from_db_chat_open_status(self.chat_owner_slug)
                        and self.scope['user'].allowed_run_chat):
                    await self._set_chat_open_status(True)
            case "close_chat":
                if await cache_manager.get_or_set_from_db_chat_open_status(self.chat_owner_slug):
                    await self._set_chat_open_status(False)
            case "ban_chat":
                await self._ban_chat()

    async def _set_chat_open_status(self, is_open):
        # Setting open status to db and cache
        chat_owner = self.scope['user']
        chat_owner.is_running_chat = is_open
        await chat_owner.asave()
        RedisChatStatusInterface.update_chat_state(chat_owner)

        # Sending system message to chat
        command = "open_chat" if is_open else "close_chat"
        action = "opened" if is_open else "closed"
        message = f"{chat_owner.username} {action} chat"

        RedisChatLogInterface.log_chat_message(chat_owner_slug=self.chat_owner_slug,
                                               author_username='',
                                               author_slug='',
                                               message=message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'system_message',
             'command': command,
             'message': message},
        )

    async def _ban_chat(self):

        if not self.scope['user'].is_staff:
            return

        try:
            chat_owner = await database_sync_to_async(User.objects.get)(username_slug=self.chat_owner_slug)
        except ObjectDoesNotExist:
            return

        # Setting open status to db and cache, ban of chat owner to db
        chat_owner.is_running_chat = False
        chat_owner.allowed_run_chat = False
        await chat_owner.asave()
        RedisChatStatusInterface.update_chat_state(chat_owner)

        # Sending system message to chat
        message = f"{chat_owner.username} is banned by {self.scope['user'].username}. Chat is closed."

        RedisChatLogInterface.log_chat_message(chat_owner_slug=self.chat_owner_slug,
                                               author_username='',
                                               author_slug='',
                                               message=message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'system_message',
             'command': 'ban_chat',
             'message': message},
        )

    async def system_message(self, event):
        await self.send(text_data=json.dumps({'message': event['message'],
                                              'command': event['command'],
                                              'messageType': 'system_message'}))
