import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, ChatParticipant

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update user status
        await self.update_user_status('active')
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Update user status
        await self.update_user_status('offline')
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'typing':
            await self.handle_typing(text_data_json)
        elif message_type == 'user_status':
            await self.handle_user_status(text_data_json)
    
    async def handle_chat_message(self, data):
        message_content = data['message']
        user = self.scope['user']
        
        if not user.is_authenticated:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Authentication required'
            }))
            return
        
        # Save message to database
        message = await self.save_message(user, message_content)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': {
                        'id': user.id,
                        'alias': user.alias,
                    },
                    'created_at': message.created_at.isoformat(),
                }
            }
        )
    
    async def handle_typing(self, data):
        user = self.scope['user']
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing',
                'user': {
                    'id': user.id,
                    'alias': user.alias,
                },
                'is_typing': data.get('is_typing', True)
            }
        )
    
    async def handle_user_status(self, data):
        status = data.get('status', 'active')
        await self.update_user_status(status)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user': {
                    'id': self.scope['user'].id,
                    'alias': self.scope['user'].alias,
                },
                'status': status
            }
        )
    
    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))
    
    async def typing(self, event):
        # Send typing indicator to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user': event['user'],
            'is_typing': event['is_typing']
        }))
    
    async def user_status(self, event):
        # Send user status update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user': event['user'],
            'status': event['status']
        }))
    
    @database_sync_to_async
    def save_message(self, user, content):
        """Save message to database"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            message = Message.objects.create(
                room=room,
                sender=user,
                content=content
            )
            return message
        except ChatRoom.DoesNotExist:
            return None
    
    @database_sync_to_async
    def update_user_status(self, status):
        """Update user status in room"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            participant, created = ChatParticipant.objects.get_or_create(
                user=self.scope['user'],
                room=room
            )
            participant.status = status
            participant.save()
        except ChatRoom.DoesNotExist:
            pass
