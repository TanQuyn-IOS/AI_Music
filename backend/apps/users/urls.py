from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    # QUAN TRỌNG: '/follow/' phải đứng TRƯỚC '<str:username>/' để tránh bị shadow
    path('users/<str:username>/follow/', views.FollowToggleView.as_view(), name='follow-toggle'),
    path('users/<str:username>/', views.UserDetailView.as_view(), name='user-detail'),
]
