import datetime
import json
import re

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone

from account.models import User
from multychats.settings import PRIVATE_MESSAGE_REGEX, CHAT_USER_STATUSES, GLOBAL_CHANNELS_GROUP_NAME
from . import cache_manager
from chat.redis_interface import RedisChatLogInterface, RedisChatStatusInterface
from .models import Ban


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

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
            case "demote_moderator":
                await self._demote_moderator(text_data_json)
            case "appoint_moderator":
                await self._appoint_moderator(text_data_json)
            case "ban_user":
                await self._ban_user(text_data_json)

    async def _handle_chat_message(self, text_data_json):
        if self._banned:
            return

        if not await cache_manager.get_or_set_from_db_chat_open_status(self.chat_owner_username):
            return

        message = text_data_json.get('message')
        if not message:
            return

        sender_username = self.scope['user'].username
        sender_status = self._get_status()

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
                                               author_status=sender_status,
                                               message=message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chatroom_message',
             'message': message,
             "sender_username": sender_username,
             'sender_status': sender_status},
        )

    async def chatroom_message(self, event):
        message = event['message']
        sender_username = event['sender_username']
        sender_status = event['sender_status']

        if sender_username in self._black_list_usernames:
            return

        await self.send(text_data=json.dumps({'message': message,
                                              'senderUsername': sender_username,
                                              'senderStatus': sender_status,
                                              'messageType': 'chatroom_message'}))

    async def system_message(self, event):
        match event['command']:
            case 'demote_moderator':
                if self.scope['user'].username == event['userUsername'] and self._moderator:
                    self._moderator = False
            case 'appoint_moderator':
                if self.scope['user'].username == event['userUsername'] and not self._moderator:
                    self._moderator = True
            case 'ban_user':
                if event['userUsername'] == self.scope['user'].username:
                    self._banned = True

        await self.send(text_data=json.dumps({'message': event.get('message'),
                                              'command': event['command'],
                                              'userUsername': event.get('userUsername'),
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
                                               author_status='',
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
                                               author_status='',
                                               message=message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'system_message',
             'command': 'ban_chat',
             'message': message},
        )

    async def _add_user_to_black_list(self, text_data_json):
        username = text_data_json.get('username')

        if username in self._black_list_usernames:
            return

        try:
            black_listed_user = await User.objects.aget(username=username)
        except ObjectDoesNotExist:
            return

        await self.scope['user'].black_listed_users.aadd(black_listed_user)
        self._black_list_usernames.add(username)

        await self.send(text_data=json.dumps({'command': 'add_user_to_black_list',
                                              'userUsername': username,
                                              'messageType': 'system_message'}))

    async def _demote_moderator(self, text_data_json):
        username = text_data_json.get('username')

        try:
            moderator = await User.objects.aget(username=username)
        except ObjectDoesNotExist:
            return

        # check if user is admin or not moderator
        if moderator.is_staff:
            return
        if not await database_sync_to_async(
                moderator.moderating_user_chats.filter(username=self.scope['user'].username).exists)():
            return

        await self.scope['user'].moderators.aremove(moderator)

        RedisChatLogInterface.change_user_status(chat_owner_username=self.chat_owner_username,
                                                 username=username,
                                                 new_status=CHAT_USER_STATUSES[4])

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'system_message',
             'command': 'demote_moderator',
             'userUsername': username},
        )

    async def _appoint_moderator(self, text_data_json):
        username = text_data_json.get('username')

        try:
            moderator = await User.objects.aget(username=username)
        except ObjectDoesNotExist:
            return

        # check if user is moderator or admin
        if moderator.is_staff:
            return
        if await database_sync_to_async(
                moderator.moderating_user_chats.filter(username=self.scope['user'].username).exists)():
            return

        await self.scope['user'].moderators.aadd(moderator)

        RedisChatLogInterface.change_user_status(chat_owner_username=self.chat_owner_username,
                                                 username=username,
                                                 new_status=CHAT_USER_STATUSES[3])

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'system_message',
             'command': 'appoint_moderator',
             'userUsername': username},
        )

    async def _ban_user(self, text_data_json):
        # Check having banning permission
        if not (self._moderator
                or self.scope['user'].username == self.chat_owner_username
                or self.scope['user'].is_staff):
            return

        # getting users models
        chat_owner_slug = self.scope['url_route']['kwargs']['chat_owner_slug']
        banned_user_username = text_data_json.get('username')
        try:
            banned_user = await User.objects.aget(username=banned_user_username)
            chat_owner = await User.objects.aget(username_slug=chat_owner_slug)
        except ObjectDoesNotExist:
            return

        banned_user_is_moderator = await database_sync_to_async(
            banned_user.moderating_user_chats.filter(username_slug=chat_owner_slug).exists)()

        # checking permissions to ban this specific user
        if self._moderator and not self.scope['user'].is_staff:
            if banned_user.is_staff or banned_user == chat_owner or banned_user_is_moderator:
                return
        if (self.scope['user'].username != self.chat_owner_username and
                not self.scope['user'].is_superuser and banned_user.is_staff):
            return

        # getting and checkboxes
        ban_indefinitely = text_data_json.get('indefinitely')
        if ban_indefinitely and not (self.scope['user'].is_staff or self.scope['user'] == chat_owner):
            return
        in_all_chats = text_data_json.get('inAllChats')
        if in_all_chats and not self.scope['user'].is_staff:
            return

        # getting terms od ban and converting to minutes, or setting None if it is indefinite
        if ban_indefinitely:
            time_end = None
            message_ban_duration = "indefinite"
        else:
            ban_duration = text_data_json.get('termOfBan')
            ban_duration_type = text_data_json.get('termTypeOfBan')
            match ban_duration_type:
                case 'minutes':
                    ban_timedelta = datetime.timedelta(minutes=ban_duration)
                case 'hours':
                    ban_timedelta = datetime.timedelta(hours=ban_duration)
                case 'days':
                    ban_timedelta = datetime.timedelta(days=ban_duration)
                case _:
                    return

            # ban duration verification
            if not datetime.timedelta(minutes=20) <= ban_timedelta <= datetime.timedelta(days=30):
                return

            time_end = datetime.datetime.now() + ban_timedelta
            message_ban_duration = f"for {ban_duration} {ban_duration_type}"

        await Ban.objects.acreate(banned_user=banned_user,
                                  chat_owner=None if in_all_chats else chat_owner,
                                  banned_by=self.scope['user'],
                                  time_end=time_end)

        # clearing log, deleting banned user messages
        RedisChatLogInterface.delete_user_messages(
            chat_owner_username=None if in_all_chats else self.chat_owner_username,
            username=banned_user_username,
        )

        # creating ang logging system message
        message = f"{self.scope['user'].username} banned {banned_user_username} {message_ban_duration}"
        if in_all_chats:
            message += " in all chats"
        RedisChatLogInterface.log_chat_message(chat_owner_username=self.chat_owner_username,
                                               author_username='',
                                               author_status='',
                                               message=message)

        await self.channel_layer.group_send(
            GLOBAL_CHANNELS_GROUP_NAME if in_all_chats else self.room_group_name,
            {'type': 'system_message',
             'command': 'ban_user',
             'userUsername': banned_user_username,
             'message': message,
             },
        )

    def _get_status(self):
        if self.scope['user'].is_superuser:
            return CHAT_USER_STATUSES[0]
        if self.scope['user'].is_staff:
            return CHAT_USER_STATUSES[1]
        if self.scope['user'].username == self.chat_owner_username:
            return CHAT_USER_STATUSES[2]
        if self._moderator:
            return CHAT_USER_STATUSES[3]
        return CHAT_USER_STATUSES[4]
