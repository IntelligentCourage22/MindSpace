from django.urls import path
from . import views

urlpatterns = [
    path('entries/', views.JournalEntryListCreateView.as_view(), name='journal_entries'),
    path('entries/<int:pk>/', views.JournalEntryDetailView.as_view(), name='journal_entry_detail'),
    path('stats/', views.journal_stats, name='journal_stats'),
    path('chart-data/', views.mood_chart_data, name='mood_chart_data'),
    path('weekly-summary/', views.weekly_summary, name='weekly_summary'),
    path('entry/', views.create_or_update_entry, name='create_or_update_entry'),
]
