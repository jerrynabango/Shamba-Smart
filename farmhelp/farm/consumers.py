import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import DirectMessage
from django.contrib.auth import get_user_model

User = get_user_model()


class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['user'].username
        self.room_group_name = f'direct_message_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        receiver_username = data['receiver']

        receiver = User.objects.get(username=receiver_username)
        sender = self.scope['user']

        new_message = DirectMessage.objects.create(sender=sender,
                                                   receiver=receiver,
                                                   message=message)

        await self.channel_layer.group_send(
            f'direct_message_{receiver_username}',
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))
