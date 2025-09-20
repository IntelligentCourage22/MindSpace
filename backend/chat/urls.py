from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.ChatRoomListCreateView.as_view(), name='chat_room_list_create'),
    path('rooms/<int:pk>/', views.ChatRoomDetailView.as_view(), name='chat_room_detail'),
    path('rooms/<int:room_id>/join/', views.join_room, name='join_room'),
    path('rooms/<int:room_id>/leave/', views.leave_room, name='leave_room'),
    path('rooms/<int:room_id>/messages/', views.MessageListCreateView.as_view(), name='message_list_create'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('messages/<int:message_id>/reaction/', views.toggle_message_reaction, name='toggle_message_reaction'),
    path('invitations/', views.send_invitation, name='send_invitation'),
    path('invitations/<int:invitation_id>/respond/', views.respond_to_invitation, name='respond_to_invitation'),
    path('stats/', views.chat_stats, name='chat_stats'),
    path('activity/', views.user_activity, name='user_activity'),
]
