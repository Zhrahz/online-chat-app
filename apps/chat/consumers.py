import json

from channels.generic.websocket import AsyncWebsocketConsumer



class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_id = 'chat_%s' % self.chat_id

        # Join room group
        await self.channel_layer.group_add(
            self.chat_group_id,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.chat_group_id,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        await self.channel_layer.group_send(
            self.chat_group_id,
            {
                'type': 'chat_message',
                'message': message ,
            }
        )
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message ,

        }, ensure_ascii=False))