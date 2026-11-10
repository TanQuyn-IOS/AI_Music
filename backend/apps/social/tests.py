from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.music.models import Song
from apps.social.models import Like, Comment, Post, PostLike, PostComment

User = get_user_model()


class SocialInteractionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user1', password='password123')
        self.staff_user = User.objects.create_user(username='admin_staff', password='password123', is_staff=True)
        self.song = Song.objects.create(
            title='Bài Hát Thử Nghiệm',
            artist=self.user,
            genre='pop',
            audio_url='https://example.com/audio/test.mp3',
            is_published=True
        )

    def test_song_like_toggle(self):
        self.client.force_authenticate(user=self.user)
        # Like
        res1 = self.client.post(f'/api/social/songs/{self.song.id}/like/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertTrue(res1.data['liked'])
        self.song.refresh_from_db()
        self.assertEqual(self.song.likes_count, 1)

        # Unlike
        res2 = self.client.post(f'/api/social/songs/{self.song.id}/like/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertFalse(res2.data['liked'])
        self.song.refresh_from_db()
        self.assertEqual(self.song.likes_count, 0)

    def test_song_comment_and_staff_moderation(self):
        self.client.force_authenticate(user=self.user)
        # Create comment
        res = self.client.post(f'/api/social/songs/{self.song.id}/comments/', {
            'content': 'Giai điệu rất hay!'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        comment_id = res.data['id']

        # Staff user should be able to delete any toxic or inappropriate comment
        self.client.force_authenticate(user=self.staff_user)
        del_res = self.client.delete(f'/api/social/comments/{comment_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_post_creation_and_comment_lifecycle(self):
        self.client.force_authenticate(user=self.user)
        # Create post
        post_res = self.client.post('/api/social/posts/', {
            'content': 'Chào mọi người, bài hát mới của mình đã ra mắt! #sonavia'
        }, format='json')
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)
        post_id = post_res.data['id']

        # Comment on post
        cmt_res = self.client.post(f'/api/social/posts/{post_id}/comment/', {
            'content': 'Chúc mừng nhé!'
        }, format='json')
        self.assertEqual(cmt_res.status_code, status.HTTP_201_CREATED)
        post_cmt_id = cmt_res.data['id']

        # Delete post comment
        del_cmt_res = self.client.delete(f'/api/social/post-comments/{post_cmt_id}/')
        self.assertEqual(del_cmt_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PostComment.objects.filter(id=post_cmt_id).exists())

