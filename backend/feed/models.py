from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator

User = get_user_model()


class Post(models.Model):
    """Community post model for anonymous sharing"""
    
    POST_CATEGORIES = [
        ('general', 'General'),
        ('support', 'Support'),
        ('celebration', 'Celebration'),
        ('advice', 'Advice'),
        ('vent', 'Vent'),
        ('gratitude', 'Gratitude'),
        ('question', 'Question'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(
        validators=[
            MinLengthValidator(10, message="Post must be at least 10 characters long"),
            MaxLengthValidator(2000, message="Post cannot exceed 2000 characters")
        ]
    )
    category = models.CharField(max_length=20, choices=POST_CATEGORIES, default='general')
    
    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    hugs_count = models.PositiveIntegerField(default=0)
    support_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    is_anonymous = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Moderation
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.CharField(max_length=100, blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.user.alias} - {self.content[:50]}..."
    
    @property
    def total_reactions(self):
        return self.likes_count + self.hugs_count + self.support_count
    
    @property
    def display_alias(self):
        return self.user.alias if self.is_anonymous else "Anonymous"


class PostReaction(models.Model):
    """Track user reactions to posts"""
    
    REACTION_TYPES = [
        ('like', 'Like'),
        ('hug', 'Hug'),
        ('support', 'Support'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post', 'reaction_type']
    
    def __str__(self):
        return f"{self.user.alias} {self.reaction_type}s {self.post.id}"


class Comment(models.Model):
    """Comments on posts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(
        validators=[
            MinLengthValidator(1, message="Comment cannot be empty"),
            MaxLengthValidator(500, message="Comment cannot exceed 500 characters")
        ]
    )
    
    # Engagement
    likes_count = models.PositiveIntegerField(default=0)
    
    # Moderation
    is_flagged = models.BooleanField(default=False)
    moderated_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.alias} on {self.post.id}: {self.content[:30]}..."


class CommentReaction(models.Model):
    """Track user reactions to comments"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_reactions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
    
    def __str__(self):
        return f"{self.user.alias} likes comment {self.comment.id}"


class PostTag(models.Model):
    """Tags for posts"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class PostTagging(models.Model):
    """Many-to-many relationship between posts and tags"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_tags')
    tag = models.ForeignKey(PostTag, on_delete=models.CASCADE, related_name='tagged_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'tag']
    
    def __str__(self):
        return f"{self.post.id} tagged with {self.tag.name}"


class FeedActivity(models.Model):
    """Track user activity in the feed"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_activities')
    activity_type = models.CharField(max_length=20, choices=[
        ('post_created', 'Post Created'),
        ('comment_made', 'Comment Made'),
        ('reaction_given', 'Reaction Given'),
        ('post_viewed', 'Post Viewed'),
    ])
    target_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    target_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.alias} - {self.activity_type}"
