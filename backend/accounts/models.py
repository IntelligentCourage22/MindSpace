from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string


def generate_random_alias():
    """Generate a random alias like BluePhoenix123"""
    adjectives = [
        'Blue', 'Green', 'Red', 'Purple', 'Golden', 'Silver', 'Bright', 'Dark',
        'Swift', 'Gentle', 'Brave', 'Kind', 'Wise', 'Calm', 'Strong', 'Peaceful',
        'Serene', 'Hopeful', 'Radiant', 'Luminous', 'Tranquil', 'Harmonious'
    ]
    nouns = [
        'Phoenix', 'Dragon', 'Eagle', 'Wolf', 'Bear', 'Lion', 'Tiger', 'Fox',
        'Owl', 'Dove', 'Butterfly', 'Star', 'Moon', 'Sun', 'Ocean', 'Mountain',
        'River', 'Forest', 'Garden', 'Flower', 'Tree', 'Cloud'
    ]
    
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    number = random.randint(10, 999)
    
    return f"{adjective}{noun}{number}"


class User(AbstractUser):
    """Custom User model with anonymous alias support"""
    email = models.EmailField(unique=True, blank=True, null=True)
    alias = models.CharField(max_length=50, unique=True, default=generate_random_alias)
    is_anonymous_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Profile fields
    bio = models.TextField(blank=True, max_length=500)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Wellness tracking
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    total_journal_entries = models.PositiveIntegerField(default=0)
    
    # Preferences
    interests = models.JSONField(default=list, blank=True)
    privacy_level = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends Only'),
            ('private', 'Private'),
        ],
        default='public'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.alias
    
    def save(self, *args, **kwargs):
        if not self.alias:
            self.alias = generate_random_alias()
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """Extended user profile for additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Mental health preferences
    mood_tracking_enabled = models.BooleanField(default=True)
    journal_reminders = models.BooleanField(default=True)
    community_participation = models.BooleanField(default=True)
    
    # Wellness goals
    wellness_goals = models.JSONField(default=list, blank=True)
    current_challenges = models.JSONField(default=list, blank=True)
    
    # Support preferences
    seeking_support = models.BooleanField(default=False)
    offering_support = models.BooleanField(default=False)
    support_topics = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.alias}'s Profile"
