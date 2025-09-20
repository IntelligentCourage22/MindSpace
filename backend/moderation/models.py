from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Report(models.Model):
    """Report model for flagging inappropriate content"""
    
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('hate_speech', 'Hate Speech'),
        ('self_harm', 'Self-Harm Content'),
        ('violence', 'Violence'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    # Content being reported
    content_type = models.CharField(max_length=20, choices=[
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('user', 'User'),
    ])
    content_id = models.PositiveIntegerField()  # ID of the reported content
    
    # Reporter
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    
    # Report details
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True, help_text="Additional details about the report")
    
    # Status and resolution
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderator = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='moderated_reports'
    )
    moderator_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['content_type', 'content_id', 'reporter']
    
    def __str__(self):
        return f"Report #{self.id} - {self.get_reason_display()} by {self.reporter.alias}"
    
    def save(self, *args, **kwargs):
        if self.status == 'reviewed' and not self.reviewed_at:
            self.reviewed_at = timezone.now()
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)


class ModerationAction(models.Model):
    """Actions taken by moderators"""
    
    ACTION_TYPES = [
        ('content_removed', 'Content Removed'),
        ('content_hidden', 'Content Hidden'),
        ('user_warned', 'User Warned'),
        ('user_suspended', 'User Suspended'),
        ('user_banned', 'User Banned'),
        ('report_dismissed', 'Report Dismissed'),
        ('content_approved', 'Content Approved'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='actions')
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.moderator.alias} - {self.get_action_type_display()}"


class ContentFlag(models.Model):
    """Automatic content flags based on keywords or patterns"""
    
    FLAG_TYPES = [
        ('keyword', 'Keyword Match'),
        ('pattern', 'Pattern Match'),
        ('ai_detection', 'AI Detection'),
        ('sentiment', 'Sentiment Analysis'),
    ]
    
    content_type = models.CharField(max_length=20, choices=[
        ('post', 'Post'),
        ('comment', 'Comment'),
    ])
    content_id = models.PositiveIntegerField()
    flag_type = models.CharField(max_length=20, choices=FLAG_TYPES)
    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    matched_pattern = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    
    # Status
    is_active = models.BooleanField(default=True)
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_flags'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-confidence_score', '-created_at']
    
    def __str__(self):
        return f"Flag #{self.id} - {self.get_flag_type_display()} ({self.confidence_score:.2f})"


class ModerationQueue(models.Model):
    """Queue for content awaiting moderation"""
    
    QUEUE_TYPES = [
        ('reported', 'Reported Content'),
        ('flagged', 'Flagged Content'),
        ('new_user', 'New User Content'),
        ('high_engagement', 'High Engagement Content'),
    ]
    
    content_type = models.CharField(max_length=20, choices=[
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('user', 'User'),
    ])
    content_id = models.PositiveIntegerField()
    queue_type = models.CharField(max_length=20, choices=QUEUE_TYPES)
    priority = models.IntegerField(default=0)  # Higher number = higher priority
    
    # Content metadata
    content_preview = models.TextField(blank=True)
    user_alias = models.CharField(max_length=50, blank=True)
    
    # Status
    is_processed = models.BooleanField(default=False)
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_queue_items'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"Queue #{self.id} - {self.get_queue_type_display()} ({self.content_type})"


class ModerationStats(models.Model):
    """Statistics for moderation activities"""
    
    date = models.DateField(unique=True)
    
    # Report statistics
    reports_received = models.PositiveIntegerField(default=0)
    reports_resolved = models.PositiveIntegerField(default=0)
    reports_dismissed = models.PositiveIntegerField(default=0)
    
    # Content statistics
    content_removed = models.PositiveIntegerField(default=0)
    content_hidden = models.PositiveIntegerField(default=0)
    users_warned = models.PositiveIntegerField(default=0)
    users_suspended = models.PositiveIntegerField(default=0)
    users_banned = models.PositiveIntegerField(default=0)
    
    # Flag statistics
    flags_generated = models.PositiveIntegerField(default=0)
    flags_reviewed = models.PositiveIntegerField(default=0)
    false_positives = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    avg_resolution_time = models.DurationField(null=True, blank=True)
    moderator_activity = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Moderation Stats - {self.date}"
