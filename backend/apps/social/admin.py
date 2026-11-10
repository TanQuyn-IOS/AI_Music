from django.contrib import admin
from .models import Like, Comment, Post, PostLike, PostComment


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'song', 'created_at']
    search_fields = ['user__username', 'song__title']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'song', 'content', 'created_at']
    search_fields = ['user__username', 'song__title', 'content']
    list_filter = ['created_at']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'content_preview', 'likes_count', 'comments_count', 'created_at']
    search_fields = ['author__username', 'content']
    list_filter = ['created_at']

    def content_preview(self, obj):
        return obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
    content_preview.short_description = 'Nội dung'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    search_fields = ['user__username']


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content', 'created_at']
    search_fields = ['user__username', 'content']
