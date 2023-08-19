import json

from channels.generic.websocket import AsyncWebsocketConsumer


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
        message = text_data_json.get('message')
        sender_username = text_data_json.get('userUsername')

        if not message or not sender_username:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chatroom_message', 'message': message, "sender_username": sender_username},
        )

    async def chatroom_message(self, event):
        message = event['message']
        sender_username = event['sender_username']

        await self.send(text_data=json.dumps({'message': message, 'senderUsername': sender_username}))
