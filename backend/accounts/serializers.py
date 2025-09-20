from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'alias', 'bio')
        extra_kwargs = {
            'email': {'required': False},
            'alias': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'alias', 'is_anonymous_user', 'bio', 'avatar',
            'current_streak', 'longest_streak', 'total_journal_entries',
            'interests', 'privacy_level', 'created_at', 'profile'
        )
        read_only_fields = ('id', 'created_at', 'current_streak', 'longest_streak', 'total_journal_entries')
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'mood_tracking_enabled': profile.mood_tracking_enabled,
                'journal_reminders': profile.journal_reminders,
                'community_participation': profile.community_participation,
                'wellness_goals': profile.wellness_goals,
                'current_challenges': profile.current_challenges,
                'seeking_support': profile.seeking_support,
                'offering_support': profile.offering_support,
                'support_topics': profile.support_topics,
            }
        except UserProfile.DoesNotExist:
            return None


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')


class AnonymousUserSerializer(serializers.Serializer):
    """Serializer for anonymous user creation"""
    alias = serializers.CharField(required=False)
    
    def create(self, validated_data):
        # Create anonymous user with random alias
        user = User.objects.create_user(
            username=f"anon_{User.objects.count() + 1}",
            is_anonymous_user=True
        )
        UserProfile.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates"""
    
    class Meta:
        model = UserProfile
        fields = (
            'mood_tracking_enabled', 'journal_reminders', 'community_participation',
            'wellness_goals', 'current_challenges', 'seeking_support',
            'offering_support', 'support_topics'
        )
