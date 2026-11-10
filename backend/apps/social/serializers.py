from rest_framework import serializers
from .models import Like, Comment, Post, PostLike, PostComment, Notification, DirectMessage
from apps.users.serializers import UserSerializer
from apps.music.models import Song
from apps.music.serializers import SongSerializer


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    song_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'song_id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'song', 'content', 'parent', 'replies', 'created_at']
        read_only_fields = ['id', 'created_at', 'song']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True, context=self.context).data
        return []

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PostCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PostComment
        fields = ['id', 'user', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    song = SongSerializer(read_only=True)
    song_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    likes_count = serializers.ReadOnlyField()
    comments_count = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    post_comments = PostCommentSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'song', 'song_id', 'image', 'image_url',
            'likes_count', 'comments_count', 'is_liked', 'post_comments', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'image': {'write_only': True}}

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.post_likes.filter(user=request.user).exists()
        return False

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def to_internal_value(self, data):
        ret = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'song' in ret and 'song_id' not in ret:
            raw_song = ret.get('song')
            if raw_song and str(raw_song).strip() not in ('', 'null', 'undefined'):
                try:
                    ret['song_id'] = int(raw_song)
                except (ValueError, TypeError):
                    pass
        return super().to_internal_value(ret)

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        song_id = validated_data.pop('song_id', None)
        if song_id is not None:
            try:
                validated_data['song'] = Song.objects.get(pk=song_id)
            except Exception:
                validated_data['song'] = None
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'actor', 'verb', 'target_id',
            'target_type', 'text', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'recipient']


class DirectMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = DirectMessage
        fields = ['id', 'sender', 'recipient', 'content', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at', 'sender', 'recipient']
