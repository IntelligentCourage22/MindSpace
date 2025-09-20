from rest_framework import serializers
from .models import Report, ModerationAction, ContentFlag, ModerationQueue, ModerationStats
from accounts.serializers import UserSerializer


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for reports"""
    reporter = UserSerializer(read_only=True)
    moderator = UserSerializer(read_only=True)
    
    class Meta:
        model = Report
        fields = (
            'id', 'content_type', 'content_id', 'reporter', 'reason',
            'description', 'status', 'moderator', 'moderator_notes',
            'created_at', 'reviewed_at', 'resolved_at'
        )
        read_only_fields = (
            'id', 'reporter', 'moderator', 'created_at', 'reviewed_at', 'resolved_at'
        )


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reports"""
    
    class Meta:
        model = Report
        fields = ('content_type', 'content_id', 'reason', 'description')
    
    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class ModerationActionSerializer(serializers.ModelSerializer):
    """Serializer for moderation actions"""
    moderator = UserSerializer(read_only=True)
    
    class Meta:
        model = ModerationAction
        fields = (
            'id', 'report', 'moderator', 'action_type', 'description',
            'metadata', 'created_at'
        )
        read_only_fields = ('id', 'moderator', 'created_at')


class ContentFlagSerializer(serializers.ModelSerializer):
    """Serializer for content flags"""
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ContentFlag
        fields = (
            'id', 'content_type', 'content_id', 'flag_type', 'confidence_score',
            'matched_pattern', 'description', 'is_active', 'is_reviewed',
            'reviewed_by', 'created_at', 'reviewed_at'
        )
        read_only_fields = ('id', 'reviewed_by', 'created_at', 'reviewed_at')


class ModerationQueueSerializer(serializers.ModelSerializer):
    """Serializer for moderation queue"""
    processed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ModerationQueue
        fields = (
            'id', 'content_type', 'content_id', 'queue_type', 'priority',
            'content_preview', 'user_alias', 'is_processed', 'processed_by',
            'created_at', 'processed_at'
        )
        read_only_fields = ('id', 'processed_by', 'created_at', 'processed_at')


class ModerationStatsSerializer(serializers.ModelSerializer):
    """Serializer for moderation statistics"""
    
    class Meta:
        model = ModerationStats
        fields = (
            'id', 'date', 'reports_received', 'reports_resolved', 'reports_dismissed',
            'content_removed', 'content_hidden', 'users_warned', 'users_suspended',
            'users_banned', 'flags_generated', 'flags_reviewed', 'false_positives',
            'avg_resolution_time', 'moderator_activity', 'created_at', 'updated_at'
        )


class ReportStatsSerializer(serializers.Serializer):
    """Serializer for report statistics"""
    total_reports = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    resolved_reports = serializers.IntegerField()
    dismissed_reports = serializers.IntegerField()
    reports_this_week = serializers.IntegerField()
    reports_this_month = serializers.IntegerField()
    most_common_reason = serializers.CharField()
    avg_resolution_time = serializers.DurationField()
    moderator_performance = serializers.ListField()


class ModerationDashboardSerializer(serializers.Serializer):
    """Serializer for moderation dashboard data"""
    queue_size = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    active_flags = serializers.IntegerField()
    recent_actions = serializers.ListField()
    top_reporters = serializers.ListField()
    content_removal_rate = serializers.FloatField()
    false_positive_rate = serializers.FloatField()
    moderator_workload = serializers.DictField()
