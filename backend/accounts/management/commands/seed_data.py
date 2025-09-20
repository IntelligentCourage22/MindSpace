from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import random

from accounts.models import User, UserProfile
from journal.models import JournalEntry, JournalStreak
from feed.models import Post, Comment, PostTag, PostTagging
from chat.models import ChatRoom, Message, ChatParticipant
from moderation.models import Report

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample data for demo purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create'
        )
        parser.add_argument(
            '--entries',
            type=int,
            default=50,
            help='Number of journal entries to create'
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=30,
            help='Number of community posts to create'
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed database...')
        
        # Create users
        users = self.create_users(options['users'])
        
        # Create journal entries
        self.create_journal_entries(users, options['entries'])
        
        # Create community posts
        self.create_community_posts(users, options['posts'])
        
        # Create chat rooms
        self.create_chat_rooms(users)
        
        # Create some reports
        self.create_reports(users)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database!')
        )

    def create_users(self, num_users):
        """Create demo users with random aliases"""
        users = []
        
        # Create some anonymous users
        for i in range(num_users // 2):
            user = User.objects.create_user(
                username=f"anon_{i+1}",
                email=f"anon{i+1}@example.com",
                is_anonymous_user=True
            )
            UserProfile.objects.create(user=user)
            users.append(user)
            self.stdout.write(f'Created anonymous user: {user.alias}')
        
        # Create some registered users
        for i in range(num_users // 2):
            user = User.objects.create_user(
                username=f"user_{i+1}",
                email=f"user{i+1}@example.com",
                is_anonymous_user=False,
                bio=f"This is user {i+1}'s bio. I'm here to support others and share my journey."
            )
            UserProfile.objects.create(user=user)
            users.append(user)
            self.stdout.write(f'Created registered user: {user.alias}')
        
        return users

    def create_journal_entries(self, users, num_entries):
        """Create journal entries with realistic mood patterns"""
        moods = [1, 2, 3, 4, 5]
        mood_weights = [0.1, 0.2, 0.3, 0.3, 0.1]  # More neutral/good moods
        
        # Sample journal prompts
        prompts = [
            "Today I felt...",
            "Something that made me smile today:",
            "I'm grateful for...",
            "A challenge I faced today:",
            "How I'm feeling right now:",
            "Something I learned about myself:",
            "A moment of peace today:",
            "What I'm looking forward to:",
            "A small victory today:",
            "How I took care of myself:"
        ]
        
        # Sample content for different moods
        mood_content = {
            1: [
                "Having a really tough day. Everything feels overwhelming right now.",
                "Feeling very low today. It's hard to see the positive side of things.",
                "Struggling with my emotions today. Just trying to get through it.",
            ],
            2: [
                "Not feeling great today, but I know this will pass.",
                "Having a difficult time, but I'm trying to stay hopeful.",
                "Feeling down, but I'm reaching out for support.",
            ],
            3: [
                "A pretty neutral day. Nothing too exciting, but nothing terrible either.",
                "Just an average day. Taking things one step at a time.",
                "Feeling okay today. Nothing remarkable, but that's fine.",
            ],
            4: [
                "Had a good day today! Feeling positive and motivated.",
                "Feeling grateful for the good things in my life.",
                "Today was better than expected. Feeling hopeful.",
            ],
            5: [
                "Amazing day! Feeling incredibly grateful and happy.",
                "Having one of those days where everything just feels right.",
                "Feeling on top of the world today! So much to be thankful for.",
            ]
        }
        
        # Sample tags
        tags = [
            "gratitude", "anxiety", "depression", "self-care", "family", "work",
            "friends", "exercise", "nature", "music", "reading", "cooking",
            "meditation", "therapy", "growth", "challenge", "success", "peace"
        ]
        
        # Sample activities
        activities = [
            "went for a walk", "called a friend", "practiced meditation",
            "read a book", "listened to music", "cooked a meal",
            "exercised", "spent time in nature", "wrote in journal",
            "watched a movie", "talked to family", "tried something new"
        ]
        
        for i in range(num_entries):
            user = random.choice(users)
            mood = random.choices(moods, weights=mood_weights)[0]
            
            # Create entry for a random date in the last 30 days
            days_ago = random.randint(0, 30)
            entry_date = timezone.now().date() - timedelta(days=days_ago)
            
            # Check if user already has entry for this date
            if JournalEntry.objects.filter(user=user, date=entry_date).exists():
                continue
            
            # Generate content based on mood
            content = random.choice(mood_content[mood])
            if random.random() < 0.3:  # 30% chance to add more content
                content += f" {random.choice(prompts)} {random.choice(mood_content[mood])}"
            
            # Generate tags
            entry_tags = random.sample(tags, random.randint(1, 4))
            
            # Generate activities
            entry_activities = random.sample(activities, random.randint(1, 3))
            
            # Generate gratitude items
            gratitude_items = [
                "my health", "my family", "my friends", "a roof over my head",
                "good food", "nature", "music", "books", "my pet", "my job"
            ]
            entry_gratitude = random.sample(gratitude_items, random.randint(1, 3))
            
            entry = JournalEntry.objects.create(
                user=user,
                date=entry_date,
                text=content,
                mood=mood,
                tags=entry_tags,
                activities=entry_activities,
                gratitude_items=entry_gratitude,
                weather=random.choice(["sunny", "cloudy", "rainy", "clear", "overcast"])
            )
            
            # Update user's journal entry count
            user.total_journal_entries += 1
            user.save()
            
            # Update streak
            streak, created = JournalStreak.objects.get_or_create(user=user)
            streak.update_streak(entry_date)
            
            if i % 10 == 0:
                self.stdout.write(f'Created {i+1} journal entries...')

    def create_community_posts(self, users, num_posts):
        """Create community posts with realistic content"""
        categories = ['general', 'support', 'celebration', 'advice', 'vent', 'gratitude', 'question']
        category_weights = [0.3, 0.2, 0.15, 0.15, 0.1, 0.05, 0.05]
        
        # Sample post content
        post_templates = {
            'general': [
                "Just wanted to share that I had a good day today. Sometimes the small wins matter the most.",
                "Feeling grateful for the support I've received here. This community means so much to me.",
                "Taking it one day at a time. Some days are harder than others, but I'm learning to be patient with myself.",
            ],
            'support': [
                "If anyone is struggling today, you're not alone. I've been there and I believe in your strength.",
                "Sending virtual hugs to anyone who needs them today. You matter and you're loved.",
                "Remember that it's okay to not be okay. Take care of yourself and reach out if you need help.",
            ],
            'celebration': [
                "Small victory: I managed to get out of bed and do one thing I've been putting off. Progress!",
                "Celebrating one week of consistent self-care. It's the small steps that count.",
                "I'm proud of myself for setting boundaries today. It wasn't easy but it was necessary.",
            ],
            'advice': [
                "Something that helps me when I'm anxious: the 5-4-3-2-1 grounding technique. Try it!",
                "I've found that journaling before bed helps me process the day. Maybe it could help you too?",
                "Don't underestimate the power of a good night's sleep. It really does make a difference.",
            ],
            'vent': [
                "Having a really tough time right now. Just needed to get this off my chest.",
                "Feeling overwhelmed by everything. Sometimes it all feels like too much.",
                "Not looking for advice, just need to vent. Some days are just hard.",
            ],
            'gratitude': [
                "Grateful for this community and the support I've found here. Thank you all.",
                "Today I'm thankful for the small moments of joy that keep me going.",
                "Appreciating the people in my life who understand and support me.",
            ],
            'question': [
                "How do you all cope with anxiety? Looking for some strategies that work for you.",
                "Has anyone tried meditation? I'm curious about getting started.",
                "What are some ways you practice self-care when you're feeling down?",
            ]
        }
        
        # Create some tags
        tag_names = [
            "anxiety", "depression", "self-care", "gratitude", "support", "mental-health",
            "wellness", "mindfulness", "therapy", "growth", "community", "healing",
            "coping", "recovery", "strength", "hope", "kindness", "understanding"
        ]
        
        for tag_name in tag_names:
            PostTag.objects.get_or_create(
                name=tag_name,
                defaults={'description': f'Tag for {tag_name}'}
            )
        
        for i in range(num_posts):
            user = random.choice(users)
            category = random.choices(categories, weights=category_weights)[0]
            
            content = random.choice(post_templates[category])
            
            # Add some variety to content
            if random.random() < 0.3:
                content += " " + random.choice([
                    "What about you all? How are you doing today?",
                    "Sending love to everyone reading this.",
                    "Remember, you're doing better than you think.",
                    "One day at a time, one step at a time.",
                ])
            
            post = Post.objects.create(
                user=user,
                content=content,
                category=category,
                is_anonymous=random.choice([True, False])
            )
            
            # Add some tags to the post
            post_tags = random.sample(tag_names, random.randint(1, 3))
            for tag_name in post_tags:
                tag = PostTag.objects.get(name=tag_name)
                PostTagging.objects.get_or_create(post=post, tag=tag)
                tag.usage_count += 1
                tag.save()
            
            # Add some reactions
            num_reactions = random.randint(0, 15)
            for _ in range(num_reactions):
                reaction_user = random.choice(users)
                if reaction_user != user:  # Don't react to own posts
                    from feed.models import PostReaction
                    PostReaction.objects.get_or_create(
                        user=reaction_user,
                        post=post,
                        reaction_type=random.choice(['like', 'hug', 'support'])
                    )
            
            # Update post reaction counts
            post.likes_count = post.reactions.filter(reaction_type='like').count()
            post.hugs_count = post.reactions.filter(reaction_type='hug').count()
            post.support_count = post.reactions.filter(reaction_type='support').count()
            post.save()
            
            # Add some comments
            num_comments = random.randint(0, 8)
            for _ in range(num_comments):
                comment_user = random.choice(users)
                if comment_user != user:  # Don't comment on own posts
                    comment_content = random.choice([
                        "Thank you for sharing this. It really resonates with me.",
                        "You're not alone in this. I've been there too.",
                        "Sending you strength and support. You've got this!",
                        "This is so relatable. Thank you for being vulnerable.",
                        "I appreciate you sharing this. It helps to know others understand.",
                        "You're doing great. Keep going!",
                        "This made me feel less alone. Thank you.",
                        "I'm proud of you for sharing. That takes courage.",
                    ])
                    
                    Comment.objects.create(
                        user=comment_user,
                        post=post,
                        content=comment_content
                    )
            
            # Update post comment count
            post.comments_count = post.comments.count()
            post.save()
            
            if i % 5 == 0:
                self.stdout.write(f'Created {i+1} community posts...')

    def create_chat_rooms(self, users):
        """Create some demo chat rooms"""
        room_types = ['peer_support', 'mentor_chat', 'group_support']
        
        for i, room_type in enumerate(room_types):
            creator = random.choice(users)
            room = ChatRoom.objects.create(
                name=f"{room_type.replace('_', ' ').title()} Room {i+1}",
                room_type=room_type,
                description=f"A {room_type.replace('_', ' ')} room for community support",
                created_by=creator,
                is_private=False,
                max_participants=10
            )
            
            # Add some participants
            participants = random.sample(users, min(5, len(users)))
            room.participants.set(participants)
            
            # Create participant records
            for participant in participants:
                ChatParticipant.objects.get_or_create(
                    user=participant,
                    room=room,
                    defaults={'status': 'active'}
                )
            
            # Add some messages
            sample_messages = [
                "Hello everyone! How is everyone doing today?",
                "I'm here if anyone needs to talk. You're not alone.",
                "Thank you for creating this space. It means a lot.",
                "I'm having a tough day but being here helps.",
                "Sending positive vibes to everyone!",
                "This community is so supportive. Thank you all.",
                "If anyone needs to vent, I'm here to listen.",
                "Remember to be kind to yourselves today.",
            ]
            
            for j, message_text in enumerate(sample_messages[:random.randint(3, 8)]):
                sender = random.choice(participants)
                Message.objects.create(
                    room=room,
                    sender=sender,
                    content=message_text
                )
            
            self.stdout.write(f'Created chat room: {room.name}')

    def create_reports(self, users):
        """Create some sample reports for moderation"""
        posts = Post.objects.all()[:10]  # Get first 10 posts
        
        report_reasons = ['spam', 'harassment', 'inappropriate', 'hate_speech', 'other']
        
        for i in range(5):  # Create 5 reports
            post = random.choice(posts)
            reporter = random.choice(users)
            
            # Don't report own posts
            if reporter == post.user:
                continue
            
            Report.objects.create(
                content_type='post',
                content_id=post.id,
                reporter=reporter,
                reason=random.choice(report_reasons),
                description=random.choice([
                    "This content seems inappropriate for our community.",
                    "I believe this violates our community guidelines.",
                    "This post contains content that may be harmful.",
                    "I'm concerned about the nature of this content.",
                ])
            )
        
        self.stdout.write('Created sample reports for moderation')
