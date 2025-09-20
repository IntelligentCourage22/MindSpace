from rest_framework import serializers
from .models import (
    ChatRoom, Message, MessageReaction, ChatParticipant, 
    ChatInvitation, ChatActivity, SupportRequest
)
from accounts.serializers import UserSerializer


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for chat rooms"""
    participants = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    moderator = UserSerializer(read_only=True)
    participant_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    
    class Meta:
        model = ChatRoom
        fields = (
            'id', 'name', 'room_type', 'description', 'participants',
            'created_by', 'is_active', 'is_private', 'max_participants',
            'is_moderated', 'moderator', 'participant_count', 'is_full',
            'created_at', 'updated_at', 'last_activity'
        )
        read_only_fields = (
            'id', 'created_by', 'created_at', 'updated_at', 'last_activity'
        )


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat rooms"""
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ChatRoom
        fields = (
            'name', 'room_type', 'description', 'is_private',
            'max_participants', 'participant_ids'
        )
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids', [])
        validated_data['created_by'] = self.context['request'].user
        room = super().create(validated_data)
        
        # Add creator as participant
        room.participants.add(room.created_by)
        
        # Add other participants
        for user_id in participant_ids:
            try:
                from accounts.models import User
                user = User.objects.get(id=user_id)
                room.participants.add(user)
            except User.DoesNotExist:
                continue
        
        return room


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages"""
    sender = UserSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    user_has_reacted = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = (
            'id', 'room', 'sender', 'message_type', 'content', 'attachment',
            'reply_to', 'is_edited', 'is_deleted', 'edited_at', 'is_flagged',
            'reactions', 'user_has_reacted', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'sender', 'is_edited', 'is_deleted', 'edited_at',
            'is_flagged', 'created_at', 'updated_at'
        )
    
    def get_reply_to(self, obj):
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'content': obj.reply_to.content[:100],
                'sender': obj.reply_to.sender.alias
            }
        return None
    
    def get_reactions(self, obj):
        reaction_counts = {}
        for reaction in obj.reactions.all():
            reaction_type = reaction.reaction_type
            if reaction_type not in reaction_counts:
                reaction_counts[reaction_type] = 0
            reaction_counts[reaction_type] += 1
        return reaction_counts
    
    def get_user_has_reacted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reactions.filter(user=request.user).exists()
        return False


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    
    class Meta:
        model = Message
        fields = ('content', 'message_type', 'attachment', 'reply_to')
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        validated_data['room'] = self.context['room']
        message = super().create(validated_data)
        
        # Create activity
        ChatActivity.objects.create(
            user=message.sender,
            room=message.room,
            activity_type='message_sent',
            message=message
        )
        
        return message


class MessageReactionSerializer(serializers.ModelSerializer):
    """Serializer for message reactions"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ('id', 'message', 'user', 'reaction_type', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class ChatParticipantSerializer(serializers.ModelSerializer):
    """Serializer for chat participants"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatParticipant
        fields = (
            'id', 'user', 'room', 'status', 'joined_at', 'last_seen',
            'left_at', 'notifications_enabled', 'is_muted'
        )
        read_only_fields = ('id', 'joined_at', 'last_seen')


class ChatInvitationSerializer(serializers.ModelSerializer):
    """Serializer for chat invitations"""
    inviter = UserSerializer(read_only=True)
    invitee = UserSerializer(read_only=True)
    room = ChatRoomSerializer(read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = ChatInvitation
        fields = (
            'id', 'room', 'inviter', 'invitee', 'message', 'status',
            'expires_at', 'is_expired', 'created_at', 'responded_at'
        )
        read_only_fields = ('id', 'inviter', 'created_at', 'responded_at')


class ChatInvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat invitations"""
    
    class Meta:
        model = ChatInvitation
        fields = ('room', 'invitee', 'message')
    
    def create(self, validated_data):
        validated_data['inviter'] = self.context['request'].user
        # Set expiration to 7 days from now
        from django.utils import timezone
        from datetime import timedelta
        validated_data['expires_at'] = timezone.now() + timedelta(days=7)
        return super().create(validated_data)


class ChatActivitySerializer(serializers.ModelSerializer):
    """Serializer for chat activities"""
    user = UserSerializer(read_only=True)
    room = ChatRoomSerializer(read_only=True)
    message = MessageSerializer(read_only=True)
    
    class Meta:
        model = ChatActivity
        fields = (
            'id', 'user', 'room', 'activity_type', 'message',
            'invitation', 'metadata', 'created_at'
        )


class SupportRequestSerializer(serializers.ModelSerializer):
    """Serializer for support requests"""
    requester = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    
    class Meta:
        model = SupportRequest
        fields = (
            'id', 'room', 'requester', 'request_type', 'priority',
            'title', 'description', 'tags', 'status', 'assigned_to',
            'created_at', 'updated_at', 'resolved_at'
        )
        read_only_fields = ('id', 'requester', 'created_at', 'updated_at', 'resolved_at')


class SupportRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating support requests"""
    
    class Meta:
        model = SupportRequest
        fields = ('room', 'request_type', 'priority', 'title', 'description', 'tags')
    
    def create(self, validated_data):
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)


class ChatStatsSerializer(serializers.Serializer):
    """Serializer for chat statistics"""
    total_rooms = serializers.IntegerField()
    active_rooms = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    messages_today = serializers.IntegerField()
    support_requests = serializers.IntegerField()
    open_support_requests = serializers.IntegerField()
    avg_messages_per_room = serializers.FloatField()
    most_active_room = serializers.CharField()
    participation_rate = serializers.FloatField()
