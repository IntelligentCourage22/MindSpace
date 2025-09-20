from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.PostListCreateView.as_view(), name='post_list_create'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/<int:post_id>/comments/', views.CommentListCreateView.as_view(), name='comment_list_create'),
    path('comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment_detail'),
    path('posts/<int:post_id>/reactions/', views.toggle_post_reaction, name='toggle_post_reaction'),
    path('comments/<int:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    path('stats/', views.feed_stats, name='feed_stats'),
    path('trending/', views.trending_posts, name='trending_posts'),
    path('activity/', views.user_activity, name='user_activity'),
    path('tags/popular/', views.popular_tags, name='popular_tags'),
]
