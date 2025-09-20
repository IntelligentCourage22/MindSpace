from django.urls import path
from . import views

urlpatterns = [
    path('reports/', views.ReportListCreateView.as_view(), name='report_list_create'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/create/', views.create_report, name='create_report'),
    path('reports/<int:report_id>/resolve/', views.resolve_report, name='resolve_report'),
    path('flags/<int:flag_id>/review/', views.review_flag, name='review_flag'),
    path('queue/', views.ModerationQueueView.as_view(), name='moderation_queue'),
    path('flags/', views.ContentFlagView.as_view(), name='content_flags'),
    path('stats/', views.report_stats, name='report_stats'),
    path('dashboard/', views.moderation_dashboard, name='moderation_dashboard'),
]
