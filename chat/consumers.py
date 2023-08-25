import json
import re

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist

from account.models import User
from multychats.settings import PRIVATE_MESSAGE_REGEX
from . import cache_manager
from chat.redis_interface import RedisChatLogInterface, RedisChatStatusInterface


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        chat_owner_slug = self.scope['url_route']['kwargs']['chat_owner_slug']
        chat_owner = await User.objects.aget(username_slug=chat_owner_slug)
        self.chat_owner_username = chat_owner.username
        self.room_group_name = f'chat_{self.chat_owner_username}'
        self._black_list_usernames = await database_sync_to_async(list)(self.scope['user'].black_listed_users.
                                                                        values_list('username', flat=True))

        await self.channel_layer.group_add(
            self.room_group_name,
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

    async def _handle_chat_message(self, text_data_json):
        message = text_data_json.get('message')
        sender_username = text_data_json.get('userUsername')

        if not await cache_manager.get_or_set_from_db_chat_open_status(self.chat_owner_username):
            return

        if not message or not sender_username:
            return

        # Is this is private message
        private_message_match = re.fullmatch(PRIVATE_MESSAGE_REGEX, message)
        if private_message_match:
            message_data = private_message_match.groupdict()
            message = message_data['message'].strip()
            recipient_username = message_data['recipient_username']

            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'private_message',
                 'message': message,
                 'recipient_username': recipient_username,
                 "sender_username": sender_username},
            )
            return

        RedisChatLogInterface.log_chat_message(chat_owner_username=self.chat_owner_username,
                                               author_username=sender_username,
                                               message=message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chatroom_message',
             'message': message,
             "sender_username": sender_username},
        )

    async def chatroom_message(self, event):
        message = event['message']
        sender_username = event['sender_username']

        if sender_username in self._black_list_usernames:
            return

        await self.send(text_data=json.dumps({'message': message,
                                              'senderUsername': sender_username,
                                              'messageType': 'chatroom_message'}))

    async def system_message(self, event):
        await self.send(text_data=json.dumps({'message': event['message'],
                                              'command': event['command'],
                                              'messageType': 'system_message'}))

    async def private_message(self, event):
        message = event['message']
        sender_username = event['sender_username']
        recipient_username = event['recipient_username']

        if ((recipient_username == self.scope['user'].username or sender_username == self.scope['user'].username)
                and sender_username not in self._black_list_usernames):
            await self.send(text_data=json.dumps({'message': message,
                                                  'recipientUsername': recipient_username,
                                                  'senderUsername': sender_username,
                                                  'messageType': 'private_message'}))

    async def _handle_management_message(self, text_data_json):
        command = text_data_json.get('command')

        match command:
            case "open_chat":
                if (not await cache_manager.get_or_set_from_db_chat_open_status(self.chat_owner_username)
                        and self.scope['user'].allowed_run_chat):
                    await self._set_chat_open_status(True)
            case "close_chat":
                if await cache_manager.get_or_set_from_db_chat_open_status(self.chat_owner_username):
                    await self._set_chat_open_status(False)
            case "ban_chat":
                await self._ban_chat()
            case "add_user_to_black_list":
                await self._add_user_to_black_list(text_data_json)

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

        RedisChatLogInterface.log_chat_message(chat_owner_username=self.chat_owner_username,
                                               author_username='',
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
            chat_owner = await User.objects.aget(username=self.chat_owner_username)
        except ObjectDoesNotExist:
            return

        # Setting open status to db and cache, ban of chat owner to db
        chat_owner.is_running_chat = False
        chat_owner.allowed_run_chat = False
        await chat_owner.asave()
        RedisChatStatusInterface.update_chat_state(chat_owner)

        # Sending system message to chat
        message = f"{chat_owner.username} is banned by {self.scope['user'].username}. Chat is closed."

        RedisChatLogInterface.log_chat_message(chat_owner_username=self.chat_owner_username,
                                               author_username='',
                                               message=message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'system_message',
             'command': 'ban_chat',
             'message': message},
        )

    async def _add_user_to_black_list(self, text_data_json):
        username = text_data_json.get('username')

        if not username or username in self._black_list_usernames:
            return

        try:
            black_listed_user = await User.objects.aget(username=username)
        except ObjectDoesNotExist:
            return

        await self.scope['user'].black_listed_users.aadd(black_listed_user)
        self._black_list_usernames.append(username)

        await self.send(text_data=json.dumps({'command': 'add_user_to_black_list',
                                              'userUsername': username,
                                              'messageType': 'system_message'}))
