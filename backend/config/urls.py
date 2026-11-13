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


def debug_diagnostic(request):
    """Diagnostic endpoint to inspect live environment and detect runtime issues."""
    import sys, os, traceback
    res = {'status': 'ok', 'python': sys.version}
    try:
        import soundfile
        res['soundfile'] = soundfile.__version__
    except Exception as e:
        res['soundfile_error'] = f"{type(e).__name__}: {str(e)}"
    try:
        from apps.ai_engine.orchestrator import sonavia_orchestrator
        res['orchestrator'] = str(type(sonavia_orchestrator))
    except Exception as e:
        res['orchestrator_error'] = f"{type(e).__name__}: {str(e)}"
        res['orchestrator_trace'] = traceback.format_exc()
    if request.GET.get('test_gen') == '1':
        try:
            from apps.music.views import MusicGenerateUnifiedView
            from rest_framework.test import APIRequestFactory
            rf = APIRequestFactory()
            post_req = rf.post('/api/music/generate/', data={'prompt': 'test'}, format='json')
            view = MusicGenerateUnifiedView.as_view()
            response = view(post_req)
            res['generate_view_status'] = response.status_code
            res['generate_view_data'] = getattr(response, 'data', str(response.content)[:200])
        except Exception as e:
            res['generate_view_error'] = f"{type(e).__name__}: {str(e)}"
            res['generate_view_trace'] = traceback.format_exc()
    return JsonResponse(res)


urlpatterns = [
    path('', health_check, name='root-health'),
    path('api/health/', health_check, name='api-health'),
    path('api/debug/', debug_diagnostic, name='api-debug'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/music/', include('apps.music.urls')),
    path('api/social/', include('apps.social.urls')),
    path('api/ai/', include('apps.ai_engine.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^media/(?P<path>.*)$', serve_media_with_range, name='media-serve'),
]
