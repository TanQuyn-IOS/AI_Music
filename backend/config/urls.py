from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView
from apps.music.media_views import serve_media_with_range


def health_check(request):
    """Health check endpoint for Render and UptimeRobot monitoring."""
    return JsonResponse({
        'status': 'ok',
        'service': 'Sonavia AI Music API',
        'healthy': True
    })


urlpatterns = [
    path('', health_check, name='root-health'),
    path('api/health/', health_check, name='api-health'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/music/', include('apps.music.urls')),
    path('api/social/', include('apps.social.urls')),
    path('api/ai/', include('apps.ai_engine.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^media/(?P<path>.*)$', serve_media_with_range, name='media-serve'),
]
