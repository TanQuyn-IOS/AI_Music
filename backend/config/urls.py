from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from rest_framework_simplejwt.views import TokenRefreshView
from apps.music.media_views import serve_media_with_range

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/music/', include('apps.music.urls')),
    path('api/social/', include('apps.social.urls')),
    path('api/ai/', include('apps.ai_engine.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^media/(?P<path>.*)$', serve_media_with_range, name='media-serve'),
]

