import os
from rest_framework import serializers
from .models import Song, Playlist, PlaylistSong, ListenHistory
from apps.users.serializers import UserSerializer


class SongSerializer(serializers.ModelSerializer):
    artist = UserSerializer(read_only=True)
    likes_count = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    cover_image_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    audio_file_url = serializers.CharField(required=False, allow_blank=True, allow_null=True, read_only=True)
    audio_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    audioUrl = serializers.CharField(required=False, allow_blank=True, allow_null=True, read_only=True)

    class Meta:
        model = Song
        fields = [
            'id', 'title', 'artist', 'audio_file', 'audio_file_url', 'audio_url', 'audioUrl',
            'cover_image', 'cover_image_url', 'genre', 'mood', 'tempo',
            'duration', 'lyrics', 'description', 'play_count', 'tags',
            'is_published', 'likes_count', 'is_liked', 'created_at',
        ]
        read_only_fields = ['id', 'play_count', 'created_at']
        extra_kwargs = {
            'audio_file': {'write_only': True},
            'cover_image': {'write_only': True},
        }

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def _resolve_audio_url(self, obj):
        request = self.context.get('request')
        url = None
        if obj.audio_file:
            try:
                url = obj.audio_file.url
            except Exception:
                url = None
        elif obj.audio_url:
            url = obj.audio_url

        if url:
            if request and url.startswith('/'):
                return request.build_absolute_uri(url)
            return url
        return None

    def _resolve_cover_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image:
            try:
                if request:
                    return request.build_absolute_uri(obj.cover_image.url)
                return obj.cover_image.url
            except Exception:
                return None
        return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        resolved_audio = self._resolve_audio_url(instance)
        resolved_cover = self._resolve_cover_url(instance)
        ret['audio_file_url'] = resolved_audio
        ret['audio_url'] = resolved_audio
        ret['audioUrl'] = resolved_audio
        if resolved_cover:
            ret['cover_image_url'] = resolved_cover
        return ret

    def create(self, validated_data):
        if 'cover_image_url' in validated_data:
            # cover_image_url is not a direct model field on Song (cover_image FileField is)
            cover_url = validated_data.pop('cover_image_url', None)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['artist'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'cover_image_url' in validated_data:
            validated_data.pop('cover_image_url', None)
        return super().update(instance, validated_data)


class PlaylistSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    songs = SongSerializer(many=True, read_only=True)
    songs_count = serializers.ReadOnlyField()
    cover_image_url = serializers.SerializerMethodField()

    def to_internal_value(self, data):
        ret = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'title' in ret and 'name' not in ret:
            ret['name'] = ret['title']
        return super().to_internal_value(ret)

    class Meta:
        model = Playlist
        fields = [
            'id', 'name', 'description', 'owner', 'songs', 'songs_count',
            'cover_image', 'cover_image_url', 'is_public', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'cover_image': {'write_only': True}}

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class ListenHistorySerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    song_id = serializers.PrimaryKeyRelatedField(
        queryset=Song.objects.all(), write_only=True, source='song'
    )

    class Meta:
        model = ListenHistory
        fields = ['id', 'song', 'song_id', 'listened_at', 'duration_listened']
        read_only_fields = ['id', 'listened_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
