from rest_framework import serializers
from .models import JournalEntry, MoodSummary, JournalStreak
from accounts.serializers import UserSerializer


class JournalEntrySerializer(serializers.ModelSerializer):
    """Serializer for journal entries"""
    user = UserSerializer(read_only=True)
    mood_emoji = serializers.ReadOnlyField()
    
    class Meta:
        model = JournalEntry
        fields = (
            'id', 'user', 'date', 'text', 'mood', 'mood_emoji',
            'tags', 'weather', 'activities', 'gratitude_items',
            'word_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'word_count', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class JournalEntryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating journal entries"""
    
    class Meta:
        model = JournalEntry
        fields = ('date', 'text', 'mood', 'tags', 'weather', 'activities', 'gratitude_items')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        entry = super().create(validated_data)
        
        # Update user's journal entry count
        user = validated_data['user']
        user.total_journal_entries += 1
        user.save()
        
        # Update streak
        streak, created = JournalStreak.objects.get_or_create(user=user)
        streak.update_streak(entry.date)
        
        return entry


class MoodSummarySerializer(serializers.ModelSerializer):
    """Serializer for mood summaries"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MoodSummary
        fields = (
            'id', 'user', 'week_start', 'week_end', 'average_mood',
            'total_entries', 'mood_distribution', 'most_common_tags',
            'positive_trend', 'improvement_areas', 'created_at'
        )


class JournalStreakSerializer(serializers.ModelSerializer):
    """Serializer for journal streaks"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = JournalStreak
        fields = (
            'id', 'user', 'current_streak', 'longest_streak',
            'last_entry_date', 'milestones_achieved', 'updated_at'
        )


class JournalStatsSerializer(serializers.Serializer):
    """Serializer for journal statistics"""
    total_entries = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    average_mood_week = serializers.FloatField()
    average_mood_month = serializers.FloatField()
    mood_trend = serializers.CharField()
    most_used_tags = serializers.ListField()
    total_words = serializers.IntegerField()
    entries_this_week = serializers.IntegerField()
    entries_this_month = serializers.IntegerField()
