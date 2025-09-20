from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import JournalEntry, MoodSummary, JournalStreak
from .serializers import (
    JournalEntrySerializer, JournalEntryCreateSerializer,
    MoodSummarySerializer, JournalStreakSerializer, JournalStatsSerializer
)


class JournalEntryListCreateView(generics.ListCreateAPIView):
    """List and create journal entries"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JournalEntryCreateSerializer
        return JournalEntrySerializer
    
    def get_queryset(self):
        return JournalEntry.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class JournalEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a journal entry"""
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return JournalEntry.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def journal_stats(request):
    """Get comprehensive journal statistics"""
    user = request.user
    now = timezone.now().date()
    
    # Basic stats
    total_entries = JournalEntry.objects.filter(user=user).count()
    
    # Streak info
    try:
        streak = JournalStreak.objects.get(user=user)
        current_streak = streak.current_streak
        longest_streak = streak.longest_streak
    except JournalStreak.DoesNotExist:
        current_streak = 0
        longest_streak = 0
    
    # Time-based stats
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    entries_this_week = JournalEntry.objects.filter(
        user=user, date__gte=week_ago
    ).count()
    
    entries_this_month = JournalEntry.objects.filter(
        user=user, date__gte=month_ago
    ).count()
    
    # Mood statistics
    week_moods = JournalEntry.objects.filter(
        user=user, date__gte=week_ago
    ).values_list('mood', flat=True)
    
    month_moods = JournalEntry.objects.filter(
        user=user, date__gte=month_ago
    ).values_list('mood', flat=True)
    
    average_mood_week = sum(week_moods) / len(week_moods) if week_moods else 0
    average_mood_month = sum(month_moods) / len(month_moods) if month_moods else 0
    
    # Mood trend
    recent_moods = list(JournalEntry.objects.filter(
        user=user, date__gte=week_ago
    ).order_by('date').values_list('mood', flat=True))
    
    if len(recent_moods) >= 2:
        if recent_moods[-1] > recent_moods[0]:
            mood_trend = 'improving'
        elif recent_moods[-1] < recent_moods[0]:
            mood_trend = 'declining'
        else:
            mood_trend = 'stable'
    else:
        mood_trend = 'insufficient_data'
    
    # Tags analysis
    all_tags = []
    for entry in JournalEntry.objects.filter(user=user):
        all_tags.extend(entry.tags)
    
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    most_used_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    most_used_tags = [tag for tag, count in most_used_tags]
    
    # Total words
    total_words = sum(JournalEntry.objects.filter(user=user).values_list('word_count', flat=True))
    
    stats = {
        'total_entries': total_entries,
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'average_mood_week': round(average_mood_week, 2),
        'average_mood_month': round(average_mood_month, 2),
        'mood_trend': mood_trend,
        'most_used_tags': most_used_tags,
        'total_words': total_words,
        'entries_this_week': entries_this_week,
        'entries_this_month': entries_this_month,
    }
    
    serializer = JournalStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mood_chart_data(request):
    """Get mood data for charts"""
    user = request.user
    days = int(request.GET.get('days', 30))
    
    start_date = timezone.now().date() - timedelta(days=days)
    
    entries = JournalEntry.objects.filter(
        user=user,
        date__gte=start_date
    ).order_by('date')
    
    chart_data = []
    for entry in entries:
        chart_data.append({
            'date': entry.date.isoformat(),
            'mood': entry.mood,
            'mood_emoji': entry.mood_emoji,
            'word_count': entry.word_count,
            'tags': entry.tags,
        })
    
    return Response(chart_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def weekly_summary(request):
    """Get weekly mood summary"""
    user = request.user
    now = timezone.now().date()
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=6)
    
    entries = JournalEntry.objects.filter(
        user=user,
        date__gte=week_start,
        date__lte=week_end
    )
    
    if not entries.exists():
        return Response({'message': 'No entries this week'})
    
    # Calculate summary
    moods = [entry.mood for entry in entries]
    average_mood = sum(moods) / len(moods)
    
    # Mood distribution
    mood_distribution = {}
    for mood in range(1, 6):
        mood_distribution[mood] = moods.count(mood)
    
    # Most common tags
    all_tags = []
    for entry in entries:
        all_tags.extend(entry.tags)
    
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    most_common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    most_common_tags = [tag for tag, count in most_common_tags]
    
    # Positive trend
    if len(moods) >= 2:
        positive_trend = moods[-1] > moods[0]
    else:
        positive_trend = False
    
    summary = {
        'week_start': week_start.isoformat(),
        'week_end': week_end.isoformat(),
        'total_entries': len(entries),
        'average_mood': round(average_mood, 2),
        'mood_distribution': mood_distribution,
        'most_common_tags': most_common_tags,
        'positive_trend': positive_trend,
        'total_words': sum(entry.word_count for entry in entries),
    }
    
    return Response(summary)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_or_update_entry(request):
    """Create or update journal entry for a specific date"""
    date_str = request.data.get('date')
    if not date_str:
        return Response({'error': 'Date is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if entry exists for this date
    try:
        entry = JournalEntry.objects.get(user=request.user, date=entry_date)
        serializer = JournalEntrySerializer(entry, data=request.data, partial=True)
    except JournalEntry.DoesNotExist:
        serializer = JournalEntryCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
