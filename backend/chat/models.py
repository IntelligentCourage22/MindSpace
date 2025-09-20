from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator

User = get_user_model()


class ChatRoom(models.Model):
    """Chat room model for peer support conversations"""
    
    ROOM_TYPES = [
        ('peer_support', 'Peer Support'),
        ('mentor_chat', 'Mentor Chat'),
        ('group_support', 'Group Support'),
        ('crisis_support', 'Crisis Support'),
    ]
    
    name = models.CharField(max_length=100, blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='peer_support')
    description = models.TextField(blank=True)
    
    # Participants
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    
    # Room settings
    is_active = models.BooleanField(default=True)
    is_private = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(default=2)
    
    # Moderation
    is_moderated = models.BooleanField(default=False)
    moderator = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='moderated_rooms'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_activity']
    
    def __str__(self):
        if self.name:
            return self.name
        return f"{self.get_room_type_display()} - {self.id}"
    
    @property
    def participant_count(self):
        return self.participants.count()
    
    @property
    def is_full(self):
        return self.participant_count >= self.max_participants


class Message(models.Model):
    """Message model for chat conversations"""
    
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System'),
        ('support_request', 'Support Request'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    
    # Content
    content = models.TextField(
        validators=[
            MinLengthValidator(1, message="Message cannot be empty"),
            MaxLengthValidator(2000, message="Message cannot exceed 2000 characters")
        ]
    )
    
    # Optional fields
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    # Status
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Moderation
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.alias}: {self.content[:50]}..."
    
    def save(self, *args, **kwargs):
        if self.is_edited and not self.edited_at:
            self.edited_at = timezone.now()
        super().save(*args, **kwargs)


class MessageReaction(models.Model):
    """Reactions to messages"""
    
    REACTION_TYPES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('hug', '🤗'),
        ('support', '💪'),
        ('laugh', '😂'),
        ('sad', '😢'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user', 'reaction_type']
    
    def __str__(self):
        return f"{self.user.alias} {self.reaction_type}s message {self.message.id}"


class ChatParticipant(models.Model):
    """Track participant status in chat rooms"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('away', 'Away'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_participations')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='participations')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    # Settings
    notifications_enabled = models.BooleanField(default=True)
    is_muted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'room']
    
    def __str__(self):
        return f"{self.user.alias} in {self.room}"


class ChatInvitation(models.Model):
    """Invitations to join chat rooms"""
    
    INVITATION_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    message = models.TextField(blank=True)
    
    status = models.CharField(max_length=10, choices=INVITATION_STATUS, default='pending')
    expires_at = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['room', 'invitee']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation to {self.room} for {self.invitee.alias}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class ChatActivity(models.Model):
    """Track chat activities for analytics"""
    
    ACTIVITY_TYPES = [
        ('message_sent', 'Message Sent'),
        ('room_joined', 'Room Joined'),
        ('room_left', 'Room Left'),
        ('invitation_sent', 'Invitation Sent'),
        ('invitation_accepted', 'Invitation Accepted'),
        ('reaction_added', 'Reaction Added'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_activities')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    # Optional related objects
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    invitation = models.ForeignKey(ChatInvitation, on_delete=models.CASCADE, null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.alias} - {self.get_activity_type_display()} in {self.room}"


class SupportRequest(models.Model):
    """Support requests in chat rooms"""
    
    REQUEST_TYPES = [
        ('emotional_support', 'Emotional Support'),
        ('crisis_intervention', 'Crisis Intervention'),
        ('peer_connection', 'Peer Connection'),
        ('resource_sharing', 'Resource Sharing'),
        ('general_help', 'General Help'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='support_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Request details
    title = models.CharField(max_length=200)
    description = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], default='open')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_support_requests'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"Support Request: {self.title} by {self.requester.alias}"
