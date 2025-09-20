from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Report, ModerationAction, ContentFlag, ModerationQueue, ModerationStats
from .serializers import (
    ReportSerializer, ReportCreateSerializer, ModerationActionSerializer,
    ContentFlagSerializer, ModerationQueueSerializer, ModerationStatsSerializer,
    ReportStatsSerializer, ModerationDashboardSerializer
)


class ReportListCreateView(generics.ListCreateAPIView):
    """List and create reports"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReportCreateSerializer
        return ReportSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Report.objects.all()
        return Report.objects.filter(reporter=self.request.user)


class ReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a report"""
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Report.objects.all()
        return Report.objects.filter(reporter=self.request.user)


class ModerationQueueView(generics.ListAPIView):
    """List moderation queue items"""
    serializer_class = ModerationQueueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return ModerationQueue.objects.none()
        return ModerationQueue.objects.filter(is_processed=False)


class ContentFlagView(generics.ListAPIView):
    """List content flags"""
    serializer_class = ContentFlagSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return ContentFlag.objects.none()
        return ContentFlag.objects.filter(is_active=True, is_reviewed=False)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_report(request):
    """Create a new report"""
    serializer = ReportCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        report = serializer.save()
        
        # Add to moderation queue
        ModerationQueue.objects.create(
            content_type=report.content_type,
            content_id=report.content_id,
            queue_type='reported',
            priority=1,
            content_preview=f"Reported for: {report.get_reason_display()}",
            user_alias=report.reporter.alias
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resolve_report(request, report_id):
    """Resolve a report (staff only)"""
    if not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
    
    action_type = request.data.get('action_type')
    description = request.data.get('description', '')
    
    if not action_type:
        return Response({'error': 'Action type is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create moderation action
    action = ModerationAction.objects.create(
        report=report,
        moderator=request.user,
        action_type=action_type,
        description=description,
        metadata=request.data.get('metadata', {})
    )
    
    # Update report status
    report.status = 'resolved'
    report.moderator = request.user
    report.moderator_notes = description
    report.save()
    
    # Mark queue item as processed
    ModerationQueue.objects.filter(
        content_type=report.content_type,
        content_id=report.content_id,
        queue_type='reported'
    ).update(
        is_processed=True,
        processed_by=request.user,
        processed_at=timezone.now()
    )
    
    return Response({'message': 'Report resolved successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def review_flag(request, flag_id):
    """Review a content flag (staff only)"""
    if not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        flag = ContentFlag.objects.get(id=flag_id)
    except ContentFlag.DoesNotExist:
        return Response({'error': 'Flag not found'}, status=status.HTTP_404_NOT_FOUND)
    
    is_valid = request.data.get('is_valid', True)
    notes = request.data.get('notes', '')
    
    flag.is_reviewed = True
    flag.reviewed_by = request.user
    flag.reviewed_at = timezone.now()
    flag.is_active = is_valid
    flag.save()
    
    return Response({'message': 'Flag reviewed successfully'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def report_stats(request):
    """Get report statistics"""
    if not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    now = timezone.now().date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Basic stats
    total_reports = Report.objects.count()
    pending_reports = Report.objects.filter(status='pending').count()
    resolved_reports = Report.objects.filter(status='resolved').count()
    dismissed_reports = Report.objects.filter(status='dismissed').count()
    
    # Time-based stats
    reports_this_week = Report.objects.filter(created_at__date__gte=week_ago).count()
    reports_this_month = Report.objects.filter(created_at__date__gte=month_ago).count()
    
    # Most common reason
    reason_counts = Report.objects.values('reason').annotate(count=Count('reason')).order_by('-count')
    most_common_reason = reason_counts[0]['reason'] if reason_counts else 'other'
    
    # Average resolution time
    resolved_reports_with_time = Report.objects.filter(
        status='resolved',
        reviewed_at__isnull=False
    )
    if resolved_reports_with_time.exists():
        avg_resolution_time = resolved_reports_with_time.aggregate(
            avg_time=Avg('reviewed_at' - 'created_at')
        )['avg_time']
    else:
        avg_resolution_time = None
    
    # Moderator performance
    moderator_performance = ModerationAction.objects.values('moderator__alias').annotate(
        action_count=Count('id')
    ).order_by('-action_count')[:5]
    
    stats = {
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'resolved_reports': resolved_reports,
        'dismissed_reports': dismissed_reports,
        'reports_this_week': reports_this_week,
        'reports_this_month': reports_this_month,
        'most_common_reason': most_common_reason,
        'avg_resolution_time': avg_resolution_time,
        'moderator_performance': list(moderator_performance),
    }
    
    serializer = ReportStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def moderation_dashboard(request):
    """Get moderation dashboard data"""
    if not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Queue size
    queue_size = ModerationQueue.objects.filter(is_processed=False).count()
    
    # Pending reports
    pending_reports = Report.objects.filter(status='pending').count()
    
    # Active flags
    active_flags = ContentFlag.objects.filter(is_active=True, is_reviewed=False).count()
    
    # Recent actions
    recent_actions = ModerationAction.objects.select_related('moderator', 'report').order_by('-created_at')[:10]
    recent_actions_data = ModerationActionSerializer(recent_actions, many=True).data
    
    # Top reporters
    top_reporters = Report.objects.values('reporter__alias').annotate(
        report_count=Count('id')
    ).order_by('-report_count')[:5]
    
    # Content removal rate
    total_actions = ModerationAction.objects.count()
    removal_actions = ModerationAction.objects.filter(
        action_type__in=['content_removed', 'content_hidden']
    ).count()
    content_removal_rate = (removal_actions / max(total_actions, 1)) * 100
    
    # False positive rate
    total_flags = ContentFlag.objects.filter(is_reviewed=True).count()
    false_positives = ContentFlag.objects.filter(
        is_reviewed=True,
        is_active=False
    ).count()
    false_positive_rate = (false_positives / max(total_flags, 1)) * 100
    
    # Moderator workload
    moderator_workload = ModerationAction.objects.values('moderator__alias').annotate(
        action_count=Count('id')
    ).order_by('-action_count')
    
    dashboard_data = {
        'queue_size': queue_size,
        'pending_reports': pending_reports,
        'active_flags': active_flags,
        'recent_actions': recent_actions_data,
        'top_reporters': list(top_reporters),
        'content_removal_rate': round(content_removal_rate, 2),
        'false_positive_rate': round(false_positive_rate, 2),
        'moderator_workload': list(moderator_workload),
    }
    
    serializer = ModerationDashboardSerializer(dashboard_data)
    return Response(serializer.data)
