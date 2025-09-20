from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()


class JournalEntry(models.Model):
    """Journal entry model for mood tracking and personal reflection"""
    
    MOOD_CHOICES = [
        (1, '😢 Very Low'),
        (2, '😔 Low'),
        (3, '😐 Neutral'),
        (4, '😊 Good'),
        (5, '😄 Excellent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    date = models.DateField(default=timezone.now)
    text = models.TextField()
    mood = models.IntegerField(choices=MOOD_CHOICES)
    
    # Optional fields for enhanced tracking
    tags = models.JSONField(default=list, blank=True)
    weather = models.CharField(max_length=50, blank=True)
    activities = models.JSONField(default=list, blank=True)
    gratitude_items = models.JSONField(default=list, blank=True)
    
    # Metadata
    word_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.alias} - {self.date} ({self.get_mood_display()})"
    
    def save(self, *args, **kwargs):
        # Calculate word count
        self.word_count = len(self.text.split())
        super().save(*args, **kwargs)
    
    @property
    def mood_emoji(self):
        """Return emoji for mood"""
        mood_emojis = {1: '😢', 2: '😔', 3: '😐', 4: '😊', 5: '😄'}
        return mood_emojis.get(self.mood, '😐')


class MoodSummary(models.Model):
    """Weekly mood summary for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_summaries')
    week_start = models.DateField()
    week_end = models.DateField()
    
    # Calculated fields
    average_mood = models.FloatField()
    total_entries = models.PositiveIntegerField()
    mood_distribution = models.JSONField(default=dict)  # {1: count, 2: count, ...}
    
    # Insights
    most_common_tags = models.JSONField(default=list)
    positive_trend = models.BooleanField(default=False)
    improvement_areas = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'week_start']
        ordering = ['-week_start']
    
    def __str__(self):
        return f"{self.user.alias} - Week {self.week_start} (Avg: {self.average_mood})"


class JournalStreak(models.Model):
    """Track journaling streaks"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_streaks')
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_entry_date = models.DateField(null=True, blank=True)
    
    # Streak milestones
    milestones_achieved = models.JSONField(default=list)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user']
    
    def __str__(self):
        return f"{self.user.alias} - {self.current_streak} day streak"
    
    def update_streak(self, entry_date):
        """Update streak based on new entry date"""
        if self.last_entry_date:
            days_diff = (entry_date - self.last_entry_date).days
            
            if days_diff == 1:
                # Consecutive day
                self.current_streak += 1
            elif days_diff > 1:
                # Streak broken
                self.current_streak = 1
            # days_diff == 0 means same day, no change
        else:
            # First entry
            self.current_streak = 1
        
        self.last_entry_date = entry_date
        
        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.save()
        
        # Update user's streak
        self.user.current_streak = self.current_streak
        self.user.longest_streak = self.longest_streak
        self.user.save()
