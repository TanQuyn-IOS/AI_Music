from django.urls import path
from . import views

urlpatterns = [
    # Song interactions
    path('songs/<int:song_id>/like/', views.LikeToggleView.as_view(), name='like-toggle'),
    path('songs/<int:song_id>/comments/', views.CommentListCreateView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', views.CommentDeleteView.as_view(), name='comment-delete'),
    # Posts
    path('posts/', views.PostListCreateView.as_view(), name='post-list'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:pk>/like/', views.PostLikeToggleView.as_view(), name='post-like'),
    path('posts/<int:pk>/comment/', views.PostCommentCreateView.as_view(), name='post-comment'),
    path('post-comments/<int:pk>/', views.PostCommentDeleteView.as_view(), name='post-comment-delete'),
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/read/', views.NotificationMarkReadView.as_view(), name='notification-read'),
    path('notifications/unread-count/', views.NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    # Direct Messaging
    path('messages/conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('messages/<str:username>/', views.DirectMessageHistoryView.as_view(), name='message-history'),
    # Community / Discovery
    path('trending/posts/', views.TrendingPostsView.as_view(), name='trending-posts'),
    path('trending/tags/', views.TrendingTagsView.as_view(), name='trending-tags'),
    path('users/suggested/', views.SuggestedUsersView.as_view(), name='suggested-users'),
    path('users/active/', views.ActiveUsersView.as_view(), name='active-users'),
    path('stats/', views.CommunityStatsView.as_view(), name='community-stats'),
]
