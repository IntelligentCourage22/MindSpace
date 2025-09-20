from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    ChatRoom, Message, MessageReaction, ChatParticipant,
    ChatInvitation, ChatActivity, SupportRequest
)
from .serializers import (
    ChatRoomSerializer, ChatRoomCreateSerializer, MessageSerializer,
    MessageCreateSerializer, MessageReactionSerializer, ChatParticipantSerializer,
    ChatInvitationSerializer, ChatInvitationCreateSerializer, ChatActivitySerializer,
    SupportRequestSerializer, SupportRequestCreateSerializer, ChatStatsSerializer
)


class ChatRoomListCreateView(generics.ListCreateAPIView):
    """List and create chat rooms"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChatRoomCreateSerializer
        return ChatRoomSerializer
    
    def get_queryset(self):
        return ChatRoom.objects.filter(
            participants=self.request.user,
            is_active=True
        ).prefetch_related('participants', 'messages')


class ChatRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a chat room"""
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ChatRoom.objects.filter(participants=self.request.user)


class MessageListCreateView(generics.ListCreateAPIView):
    """List and create messages in a chat room"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        return Message.objects.filter(
            room_id=room_id,
            is_deleted=False
        ).select_related('sender').prefetch_related('reactions')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['room'] = ChatRoom.objects.get(id=self.kwargs.get('room_id'))
        return context


class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a message"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def join_room(request, room_id):
    """Join a chat room"""
    try:
        room = ChatRoom.objects.get(id=room_id)
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if room.is_full:
        return Response({'error': 'Room is full'}, status=status.HTTP_400_BAD_REQUEST)
    
    if request.user in room.participants.all():
        return Response({'error': 'Already in room'}, status=status.HTTP_400_BAD_REQUEST)
    
    room.participants.add(request.user)
    
    # Create participant record
    ChatParticipant.objects.get_or_create(
        user=request.user,
        room=room,
        defaults={'status': 'active'}
    )
    
    # Create activity
    ChatActivity.objects.create(
        user=request.user,
        room=room,
        activity_type='room_joined'
    )
    
    return Response({'message': 'Successfully joined room'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def leave_room(request, room_id):
    """Leave a chat room"""
    try:
        room = ChatRoom.objects.get(id=room_id)
    except ChatRoom.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.user not in room.participants.all():
        return Response({'error': 'Not in room'}, status=status.HTTP_400_BAD_REQUEST)
    
    room.participants.remove(request.user)
    
    # Update participant record
    try:
        participant = ChatParticipant.objects.get(user=request.user, room=room)
        participant.left_at = timezone.now()
        participant.status = 'offline'
        participant.save()
    except ChatParticipant.DoesNotExist:
        pass
    
    # Create activity
    ChatActivity.objects.create(
        user=request.user,
        room=room,
        activity_type='room_left'
    )
    
    return Response({'message': 'Successfully left room'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_message_reaction(request, message_id):
    """Toggle reaction on a message"""
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reaction_type = request.data.get('reaction_type')
    if reaction_type not in ['like', 'love', 'hug', 'support', 'laugh', 'sad']:
        return Response({'error': 'Invalid reaction type'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user already reacted with this type
    reaction, created = MessageReaction.objects.get_or_create(
        user=request.user,
        message=message,
        reaction_type=reaction_type
    )
    
    if not created:
        # Remove reaction
        reaction.delete()
        return Response({'reaction': 'removed'})
    else:
        # Add reaction
        ChatActivity.objects.create(
            user=request.user,
            room=message.room,
            activity_type='reaction_added',
            message=message,
            metadata={'reaction_type': reaction_type}
        )
        return Response({'reaction': 'added'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_invitation(request):
    """Send invitation to join a chat room"""
    serializer = ChatInvitationCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        invitation = serializer.save()
        
        # Create activity
        ChatActivity.objects.create(
            user=request.user,
            room=invitation.room,
            activity_type='invitation_sent',
            invitation=invitation
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def respond_to_invitation(request, invitation_id):
    """Respond to a chat invitation"""
    try:
        invitation = ChatInvitation.objects.get(id=invitation_id, invitee=request.user)
    except ChatInvitation.DoesNotExist:
        return Response({'error': 'Invitation not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if invitation.is_expired:
        return Response({'error': 'Invitation has expired'}, status=status.HTTP_400_BAD_REQUEST)
    
    if invitation.status != 'pending':
        return Response({'error': 'Invitation already responded to'}, status=status.HTTP_400_BAD_REQUEST)
    
    response = request.data.get('response')  # 'accept' or 'decline'
    if response not in ['accept', 'decline']:
        return Response({'error': 'Invalid response'}, status=status.HTTP_400_BAD_REQUEST)
    
    if response == 'accept':
        invitation.status = 'accepted'
        invitation.room.participants.add(request.user)
        
        # Create participant record
        ChatParticipant.objects.get_or_create(
            user=request.user,
            room=invitation.room,
            defaults={'status': 'active'}
        )
        
        # Create activity
        ChatActivity.objects.create(
            user=request.user,
            room=invitation.room,
            activity_type='invitation_accepted',
            invitation=invitation
        )
    else:
        invitation.status = 'declined'
    
    invitation.responded_at = timezone.now()
    invitation.save()
    
    return Response({'message': f'Invitation {response}ed'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_stats(request):
    """Get chat statistics"""
    user = request.user
    now = timezone.now().date()
    
    # Basic stats
    total_rooms = ChatRoom.objects.filter(participants=user).count()
    active_rooms = ChatRoom.objects.filter(
        participants=user,
        is_active=True
    ).count()
    
    # Message stats
    total_messages = Message.objects.filter(room__participants=user).count()
    messages_today = Message.objects.filter(
        room__participants=user,
        created_at__date=now
    ).count()
    
    # Support requests
    support_requests = SupportRequest.objects.filter(room__participants=user).count()
    open_support_requests = SupportRequest.objects.filter(
        room__participants=user,
        status__in=['open', 'in_progress']
    ).count()
    
    # Average messages per room
    if total_rooms > 0:
        avg_messages_per_room = total_messages / total_rooms
    else:
        avg_messages_per_room = 0
    
    # Most active room
    most_active_room = ChatRoom.objects.filter(
        participants=user
    ).annotate(
        message_count=Count('messages')
    ).order_by('-message_count').first()
    
    most_active_room_name = most_active_room.name if most_active_room else 'None'
    
    # Participation rate (rooms with messages vs total rooms)
    rooms_with_messages = ChatRoom.objects.filter(
        participants=user,
        messages__isnull=False
    ).distinct().count()
    
    participation_rate = (rooms_with_messages / max(total_rooms, 1)) * 100
    
    stats = {
        'total_rooms': total_rooms,
        'active_rooms': active_rooms,
        'total_messages': total_messages,
        'messages_today': messages_today,
        'support_requests': support_requests,
        'open_support_requests': open_support_requests,
        'avg_messages_per_room': round(avg_messages_per_room, 2),
        'most_active_room': most_active_room_name,
        'participation_rate': round(participation_rate, 2),
    }
    
    serializer = ChatStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_activity(request):
    """Get user's chat activity"""
    activities = ChatActivity.objects.filter(user=request.user).order_by('-created_at')[:20]
    serializer = ChatActivitySerializer(activities, many=True, context={'request': request})
    return Response(serializer.data)
