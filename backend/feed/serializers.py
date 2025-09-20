from rest_framework import serializers
from .models import Post, Comment, PostReaction, CommentReaction, PostTag, PostTagging, FeedActivity
from accounts.serializers import UserSerializer


class PostTagSerializer(serializers.ModelSerializer):
    """Serializer for post tags"""
    
    class Meta:
        model = PostTag
        fields = ('id', 'name', 'description', 'color', 'usage_count')


class PostSerializer(serializers.ModelSerializer):
    """Serializer for posts"""
    user = UserSerializer(read_only=True)
    display_alias = serializers.ReadOnlyField()
    total_reactions = serializers.ReadOnlyField()
    tags = PostTagSerializer(many=True, read_only=True)
    user_has_reacted = serializers.SerializerMethodField()
    user_reactions = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = (
            'id', 'user', 'content', 'category', 'display_alias',
            'likes_count', 'hugs_count', 'support_count', 'comments_count',
            'total_reactions', 'is_anonymous', 'is_pinned', 'is_featured',
            'is_flagged', 'tags', 'user_has_reacted', 'user_reactions',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user', 'likes_count', 'hugs_count', 'support_count',
            'comments_count', 'is_pinned', 'is_featured', 'is_flagged',
            'created_at', 'updated_at'
        )
    
    def get_user_has_reacted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reactions.filter(user=request.user).exists()
        return False
    
    def get_user_reactions(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return list(obj.reactions.filter(user=request.user).values_list('reaction_type', flat=True))
        return []


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts"""
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Post
        fields = ('content', 'category', 'is_anonymous', 'tag_names')
    
    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        post = super().create(validated_data)
        
        # Add tags
        for tag_name in tag_names:
            tag, created = PostTag.objects.get_or_create(
                name=tag_name.lower().strip(),
                defaults={'description': f'Tag for {tag_name}'}
            )
            PostTagging.objects.get_or_create(post=post, tag=tag)
            tag.usage_count += 1
            tag.save()
        
        # Create activity
        FeedActivity.objects.create(
            user=post.user,
            activity_type='post_created',
            target_post=post
        )
        
        return post


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments"""
    user = UserSerializer(read_only=True)
    user_has_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = (
            'id', 'user', 'content', 'likes_count', 'user_has_liked',
            'is_flagged', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'likes_count', 'is_flagged', 'created_at', 'updated_at')
    
    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reactions.filter(user=request.user).exists()
        return False


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments"""
    
    class Meta:
        model = Comment
        fields = ('content',)
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['post'] = self.context['post']
        comment = super().create(validated_data)
        
        # Update post comment count
        comment.post.comments_count += 1
        comment.post.save()
        
        # Create activity
        FeedActivity.objects.create(
            user=comment.user,
            activity_type='comment_made',
            target_post=comment.post,
            target_comment=comment
        )
        
        return comment


class PostReactionSerializer(serializers.ModelSerializer):
    """Serializer for post reactions"""
    
    class Meta:
        model = PostReaction
        fields = ('id', 'reaction_type', 'created_at')
        read_only_fields = ('id', 'created_at')


class CommentReactionSerializer(serializers.ModelSerializer):
    """Serializer for comment reactions"""
    
    class Meta:
        model = CommentReaction
        fields = ('id', 'created_at')
        read_only_fields = ('id', 'created_at')


class FeedActivitySerializer(serializers.ModelSerializer):
    """Serializer for feed activities"""
    user = UserSerializer(read_only=True)
    target_post = PostSerializer(read_only=True)
    
    class Meta:
        model = FeedActivity
        fields = (
            'id', 'user', 'activity_type', 'target_post', 'target_comment',
            'metadata', 'created_at'
        )


class PostStatsSerializer(serializers.Serializer):
    """Serializer for post statistics"""
    total_posts = serializers.IntegerField()
    total_reactions = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    most_used_category = serializers.CharField()
    most_used_tags = serializers.ListField()
    engagement_rate = serializers.FloatField()
    posts_this_week = serializers.IntegerField()
    posts_this_month = serializers.IntegerField()
