from django.urls import path
from . import views

urlpatterns = [
    # Recommendation
    path('recommend/song/<int:song_id>/', views.RecommendSimilarView.as_view(), name='recommend-similar'),
    path('recommend/user/', views.RecommendForUserView.as_view(), name='recommend-user'),
    path('recommend/mood/', views.RecommendByMoodView.as_view(), name='recommend-mood'),
    path('profile/', views.MusicProfileView.as_view(), name='music-profile'),
    path('chatbot/', views.ChatbotView.as_view(), name='chatbot'),

    # AI MIDI Composer (cũ)
    path('compose/lyrics/', views.ComposeLyricsView.as_view(), name='compose-lyrics'),
    path('compose/midi/', views.ComposeMidiView.as_view(), name='compose-midi'),
    path('compose/preview/', views.ComposePreviewView.as_view(), name='compose-preview'),
    path('compose/options/', views.ComposerOptionsView.as_view(), name='compose-options'),

    # Smart Lyrics Generator (Suno style)
    path('lyrics/generate/', views.SmartLyricsGenerateView.as_view(), name='smart-lyrics-generate'),

    # AI Music Generator (MusicGen - nhạc ngắn)
    path('generate/music/', views.MusicGenerateView.as_view(), name='generate-music'),
    path('generate/preview/', views.MusicGeneratePreviewView.as_view(), name='generate-preview'),
    path('generate/status/', views.MusicGenerateStatusView.as_view(), name='generate-status'),
    path('generate/options/', views.MusicGenerateOptionsView.as_view(), name='generate-options'),

    # Full Song Generator (Orchestrator / MusicGen — nhạc 2-3 phút)
    path('generate/full/', views.FullSongGenerateView.as_view(), name='full-generate'),
    path('generate/full/options/', views.FullSongOptionsView.as_view(), name='full-options'),
    path('generate/full/<str:job_id>/status/', views.FullSongStatusView.as_view(), name='full-status'),
    path('generate/full/<str:job_id>/download/', views.FullSongDownloadView.as_view(), name='full-download'),

    # ACE-Step Generator (HF Space, miễn phí, có giọng hát)
    path('acestep/generate/', views.AceStepGenerateView.as_view(), name='acestep-generate'),
    path('acestep/status/', views.AceStepStatusView.as_view(), name='acestep-status'),
    path('acestep/recover/', views.AceStepRecoverView.as_view(), name='acestep-recover'),

    # Phase 1: Prompt Analyzer
    path('analyze/', views.AnalyzePromptView.as_view(), name='analyze-prompt'),
    path('prompt/enhance/', views.EnhancePromptView.as_view(), name='prompt-enhance'),

    # Visual Synesthesia (Image to Music)
    path('analyze-image/', views.AnalyzeImageView.as_view(), name='analyze-image'),

    # Phase 5: Emotion Recognition (PhoBERT / Vietnamese Semantic)
    path('emotion/classify/', views.EmotionClassifyView.as_view(), name='emotion-classify'),

    # Phase 3: Smart Generate (Prompt → Analyze → Lyrics → ACE-Step → MP3)
    path('generate/smart/', views.SmartGenerateView.as_view(), name='smart-generate'),
]


