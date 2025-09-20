from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Post, Comment, PostReaction, CommentReaction, PostTag, FeedActivity
from .serializers import (
    PostSerializer, PostCreateSerializer, CommentSerializer, CommentCreateSerializer,
    PostReactionSerializer, CommentReactionSerializer, FeedActivitySerializer,
    PostStatsSerializer
)


class PostListCreateView(generics.ListCreateAPIView):
    """List and create posts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostSerializer
    
    def get_queryset(self):
        queryset = Post.objects.filter(is_flagged=False).select_related('user').prefetch_related('post_tags__tag', 'reactions')
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by tag
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(post_tags__tag__name__icontains=tag)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(content__icontains=search)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a post"""
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    """List and create comments for a post"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id, is_flagged=False).select_related('user')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['post'] = Post.objects.get(id=self.kwargs.get('post_id'))
        return context


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a comment"""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_post_reaction(request, post_id):
    """Toggle reaction on a post"""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reaction_type = request.data.get('reaction_type')
    if reaction_type not in ['like', 'hug', 'support']:
        return Response({'error': 'Invalid reaction type'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user already reacted with this type
    reaction, created = PostReaction.objects.get_or_create(
        user=request.user,
        post=post,
        reaction_type=reaction_type
    )
    
    if not created:
        # Remove reaction
        reaction.delete()
        # Update post counts
        if reaction_type == 'like':
            post.likes_count = max(0, post.likes_count - 1)
        elif reaction_type == 'hug':
            post.hugs_count = max(0, post.hugs_count - 1)
        elif reaction_type == 'support':
            post.support_count = max(0, post.support_count - 1)
        post.save()
        
        return Response({'reaction': 'removed'})
    else:
        # Add reaction
        if reaction_type == 'like':
            post.likes_count += 1
        elif reaction_type == 'hug':
            post.hugs_count += 1
        elif reaction_type == 'support':
            post.support_count += 1
        post.save()
        
        # Create activity
        FeedActivity.objects.create(
            user=request.user,
            activity_type='reaction_given',
            target_post=post,
            metadata={'reaction_type': reaction_type}
        )
        
        return Response({'reaction': 'added'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_comment_like(request, comment_id):
    """Toggle like on a comment"""
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return Response({'error': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reaction, created = CommentReaction.objects.get_or_create(
        user=request.user,
        comment=comment
    )
    
    if not created:
        # Remove like
        reaction.delete()
        comment.likes_count = max(0, comment.likes_count - 1)
        comment.save()
        return Response({'liked': False})
    else:
        # Add like
        comment.likes_count += 1
        comment.save()
        return Response({'liked': True})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def feed_stats(request):
    """Get feed statistics"""
    user = request.user
    now = timezone.now().date()
    
    # Basic stats
    total_posts = Post.objects.filter(user=user).count()
    total_reactions = sum(Post.objects.filter(user=user).values_list(
        'likes_count', 'hugs_count', 'support_count'
    ))
    total_comments = Comment.objects.filter(user=user).count()
    
    # Most used category
    category_counts = Post.objects.filter(user=user).values('category').annotate(
        count=Count('category')
    ).order_by('-count')
    most_used_category = category_counts[0]['category'] if category_counts else 'general'
    
    # Most used tags
    tag_counts = PostTag.objects.filter(tagged_posts__post__user=user).annotate(
        usage_count=Count('tagged_posts')
    ).order_by('-usage_count')[:5]
    most_used_tags = [tag.name for tag in tag_counts]
    
    # Engagement rate
    total_views = FeedActivity.objects.filter(
        target_post__user=user,
        activity_type='post_viewed'
    ).count()
    engagement_rate = (total_reactions + total_comments) / max(total_views, 1) * 100
    
    # Time-based stats
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    posts_this_week = Post.objects.filter(user=user, created_at__date__gte=week_ago).count()
    posts_this_month = Post.objects.filter(user=user, created_at__date__gte=month_ago).count()
    
    stats = {
        'total_posts': total_posts,
        'total_reactions': total_reactions,
        'total_comments': total_comments,
        'most_used_category': most_used_category,
        'most_used_tags': most_used_tags,
        'engagement_rate': round(engagement_rate, 2),
        'posts_this_week': posts_this_week,
        'posts_this_month': posts_this_month,
    }
    
    serializer = PostStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def trending_posts(request):
    """Get trending posts based on recent engagement"""
    # Posts with high engagement in the last 24 hours
    yesterday = timezone.now() - timedelta(hours=24)
    
    trending = Post.objects.filter(
        is_flagged=False,
        created_at__gte=yesterday
    ).annotate(
        engagement_score=F('likes_count') + F('hugs_count') + F('support_count') + F('comments_count')
    ).order_by('-engagement_score', '-created_at')[:10]
    
    serializer = PostSerializer(trending, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_activity(request):
    """Get user's feed activity"""
    activities = FeedActivity.objects.filter(user=request.user).order_by('-created_at')[:20]
    serializer = FeedActivitySerializer(activities, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def popular_tags(request):
    """Get popular tags"""
    tags = PostTag.objects.annotate(
        usage_count=Count('tagged_posts')
    ).order_by('-usage_count')[:20]
    
    serializer = PostTagSerializer(tags, many=True)
    return Response(serializer.data)
