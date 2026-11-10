import logging
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Max
from .models import Like, Comment, Post, PostLike, PostComment, Notification, DirectMessage
from .serializers import (
    LikeSerializer, CommentSerializer, PostSerializer, PostCommentSerializer,
    NotificationSerializer, DirectMessageSerializer
)
from apps.music.models import Song
from apps.users.models import User, Follow
from apps.users.serializers import UserSerializer

logger = logging.getLogger(__name__)


def create_notification(recipient, actor, verb, target_id=None, target_type='', text=''):
    """Tạo thông báo trong DB nếu người nhận không phải chính người thực hiện"""
    if not recipient or recipient == actor:
        return None
    try:
        return Notification.objects.create(
            recipient=recipient,
            actor=actor,
            verb=verb,
            target_id=target_id,
            target_type=target_type,
            text=text
        )
    except Exception as e:
        logger.warning(f"Error creating notification: {e}")
        return None


class LikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, song_id):
        song = get_object_or_404(Song, pk=song_id)
        like, created = Like.objects.get_or_create(user=request.user, song=song)
        if not created:
            like.delete()
            return Response({'liked': False, 'likes_count': song.likes_count})
        
        # Tạo thông báo cho tác giả bài hát
        create_notification(
            recipient=song.artist,
            actor=request.user,
            verb='like_song',
            target_id=song.id,
            target_type='song',
            text=f"đã thích bài hát '{song.title}' của bạn"
        )
        return Response({'liked': True, 'likes_count': song.likes_count})


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        song_id = self.kwargs['song_id']
        return Comment.objects.filter(song_id=song_id, parent=None).select_related('user')

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        song = get_object_or_404(Song, pk=self.kwargs['song_id'])
        comment = serializer.save(user=self.request.user, song=song)
        
        # Tạo thông báo cho tác giả bài hát
        create_notification(
            recipient=song.artist,
            actor=self.request.user,
            verb='comment_song',
            target_id=song.id,
            target_type='song',
            text=f"đã bình luận về bài hát '{song.title}': {comment.content[:50]}"
        )


class CommentDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Comment.objects.all()
        return Comment.objects.filter(user=self.request.user)


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        user_param = self.request.query_params.get('user')
        feed = self.request.query_params.get('feed')
        qs = Post.objects.select_related('author', 'song').prefetch_related('post_comments', 'post_likes')
        if user_param:
            return qs.filter(author__username=user_param)
        if feed and self.request.user.is_authenticated:
            following_ids = Follow.objects.filter(
                follower=self.request.user
            ).values_list('following_id', flat=True)
            return qs.filter(author_id__in=list(following_ids))
        return qs

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied('Bạn không có quyền chỉnh sửa bài này.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied('Bạn không có quyền xóa bài này.')
        instance.delete()


class PostLikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
            return Response({'liked': False, 'likes_count': post.likes_count})
        
        # Tạo thông báo cho tác giả bài viết
        create_notification(
            recipient=post.author,
            actor=request.user,
            verb='like_post',
            target_id=post.id,
            target_type='post',
            text="đã thích bài viết của bạn"
        )
        return Response({'liked': True, 'likes_count': post.likes_count})


class PostCommentCreateView(generics.CreateAPIView):
    serializer_class = PostCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        comment = serializer.save(user=self.request.user, post=post)
        
        # Tạo thông báo cho tác giả bài viết
        create_notification(
            recipient=post.author,
            actor=self.request.user,
            verb='comment_post',
            target_id=post.id,
            target_type='post',
            text=f"đã bình luận bài viết của bạn: {comment.content[:50]}"
        )


class PostCommentDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return PostComment.objects.all()
        return PostComment.objects.filter(user=self.request.user)


# ─── Community / Discovery APIs ───────────────────────────────────────────────

class TrendingPostsView(generics.ListAPIView):
    """Top bài đăng nhiều like/comment nhất trong 7 ngày"""
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        from datetime import timedelta
        from django.utils import timezone
        week_ago = timezone.now() - timedelta(days=7)
        return (
            Post.objects
            .filter(created_at__gte=week_ago)
            .annotate(score=Count('post_likes') + Count('post_comments'))
            .order_by('-score', '-created_at')
            .select_related('author', 'song')
            .prefetch_related('post_comments', 'post_likes')[:20]
        )

    def get_serializer_context(self):
        return {'request': self.request}


class SuggestedUsersView(APIView):
    """Gợi ý người dùng để follow: nghệ sĩ nổi bật + active users chưa follow"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get('limit', 8))

        if request.user.is_authenticated:
            following_ids = Follow.objects.filter(
                follower=request.user
            ).values_list('following_id', flat=True)
            exclude_ids = list(following_ids) + [request.user.id]
        else:
            exclude_ids = []

        suggested = (
            User.objects
            .exclude(id__in=exclude_ids)
            .annotate(
                song_count=Count('songs', distinct=True),
                follower_count=Count('followers', distinct=True),
            )
            .order_by('-follower_count', '-song_count', '-date_joined')[:limit]
        )
        serializer = UserSerializer(suggested, many=True, context={'request': request})
        return Response(serializer.data)


class TrendingTagsView(APIView):
    """Tags/hashtags phổ biến từ nội dung bài đăng"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from datetime import timedelta
        from django.utils import timezone
        import re
        week_ago = timezone.now() - timedelta(days=14)
        posts = Post.objects.filter(created_at__gte=week_ago).values_list('content', flat=True)
        tag_count = {}
        for content in posts:
            tags = re.findall(r'#(\w+)', content)
            for tag in tags:
                tag_count[tag.lower()] = tag_count.get(tag.lower(), 0) + 1
        sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:15]
        return Response([{'tag': t, 'count': c} for t, c in sorted_tags])


class CommunityStatsView(APIView):
    """Thống kê tổng quan cộng đồng"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from apps.music.models import Song as SongModel
        return Response({
            'total_users': User.objects.count(),
            'total_posts': Post.objects.count(),
            'total_songs': SongModel.objects.filter(is_published=True).count(),
            'total_artists': User.objects.filter(is_artist=True).count(),
        })


class ActiveUsersView(generics.ListAPIView):
    """Người dùng hoạt động nhiều nhất (đăng bài, có bài hát)"""
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            User.objects
            .annotate(
                post_count=Count('posts', distinct=True),
                song_count=Count('songs', distinct=True),
                follower_count=Count('followers', distinct=True),
            )
            .filter(Q(post_count__gt=0) | Q(song_count__gt=0))
            .order_by('-follower_count', '-post_count')[:20]
        )

    def get_serializer_context(self):
        return {'request': self.request}


# ─── Notifications & Direct Messaging APIs ────────────────────────────────────

class NotificationListView(generics.ListAPIView):
    """Lấy danh sách thông báo của user đăng nhập (mới nhất trước)"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related('actor')[:50]

    def get_serializer_context(self):
        return {'request': self.request}


class NotificationMarkReadView(APIView):
    """Đánh dấu thông báo đã đọc"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        notif_id = request.data.get('id')
        if notif_id:
            Notification.objects.filter(id=notif_id, recipient=request.user).update(is_read=True)
        else:
            # Mark all as read
            Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'success': True, 'unread_count': unread_count})


class NotificationUnreadCountView(APIView):
    """Lấy số lượng thông báo chưa đọc"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': unread_count})


class ConversationListView(APIView):
    """
    Danh sách các cuộc trò chuyện (Inbox) của người dùng:
    Mỗi cuộc trò chuyện gồm: partner user, tin nhắn gần nhất, số tin chưa đọc.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        me = request.user
        # Lấy tất cả tin nhắn liên quan tới user
        messages = DirectMessage.objects.filter(
            Q(sender=me) | Q(recipient=me)
        ).select_related('sender', 'recipient').order_by('-created_at')

        partners = {}
        for msg in messages:
            partner = msg.recipient if msg.sender == me else msg.sender
            if partner.id not in partners:
                # Đếm số tin nhắn chưa đọc gửi từ partner này tới me
                unread = DirectMessage.objects.filter(
                    sender=partner, recipient=me, is_read=False
                ).count()
                partners[partner.id] = {
                    'partner': UserSerializer(partner, context={'request': request}).data,
                    'last_message': {
                        'id': msg.id,
                        'content': msg.content,
                        'is_self': msg.sender == me,
                        'created_at': msg.created_at,
                    },
                    'unread_count': unread
                }

        return Response(list(partners.values()))


class DirectMessageHistoryView(APIView):
    """
    Lịch sử chat & gửi tin nhắn 1-1 với một user cụ thể.
    GET /api/social/messages/<username>/
    POST /api/social/messages/<username>/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, username):
        target = get_object_or_404(User, username=username)
        me = request.user

        # Lấy lịch sử tin nhắn
        messages = DirectMessage.objects.filter(
            (Q(sender=me) & Q(recipient=target)) | (Q(sender=target) & Q(recipient=me))
        ).select_related('sender', 'recipient').order_by('created_at')

        # Đánh dấu các tin nhắn gửi tới mình là đã đọc
        DirectMessage.objects.filter(
            sender=target, recipient=me, is_read=False
        ).update(is_read=True)

        serializer = DirectMessageSerializer(messages, many=True, context={'request': request})
        return Response({
            'target_user': UserSerializer(target, context={'request': request}).data,
            'messages': serializer.data
        })

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        me = request.user

        if target == me:
            return Response({'error': 'Không thể tự gửi tin nhắn cho chính mình.'}, status=400)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Nội dung tin nhắn không được để trống.'}, status=400)

        msg = DirectMessage.objects.create(
            sender=me,
            recipient=target,
            content=content
        )

        # Tạo thông báo đến người nhận
        create_notification(
            recipient=target,
            actor=me,
            verb='message',
            target_id=me.id,
            target_type='message',
            text=f"đã gửi tin nhắn cho bạn: {content[:40]}"
        )

        serializer = DirectMessageSerializer(msg, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
