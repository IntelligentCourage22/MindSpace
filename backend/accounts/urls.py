from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.logout, name='logout'),
    path('anonymous/', views.create_anonymous_user, name='anonymous_user'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/settings/', views.UserProfileSettingsView.as_view(), name='profile_settings'),
    path('stats/', views.user_stats, name='user_stats'),
    path('update-alias/', views.update_alias, name='update_alias'),
]
