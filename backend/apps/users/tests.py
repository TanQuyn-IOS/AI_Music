from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testartist',
            'email': 'artist@sonavia.ai',
            'password': 'SecurePassword123!',
            'is_artist': True,
        }
        self.user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            is_artist=True,
        )

    def test_user_creation_and_hashing(self):
        self.assertEqual(self.user.username, 'testartist')
        self.assertTrue(self.user.check_password('SecurePassword123!'))
        self.assertFalse(self.user.check_password('WrongPassword'))
        self.assertTrue(self.user.is_artist)

    def test_user_login_success(self):
        res = self.client.post('/api/auth/login/', {
            'username': 'testartist',
            'password': 'SecurePassword123!',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertEqual(res.data['user']['username'], 'testartist')

    def test_user_login_invalid_password(self):
        res = self.client.post('/api/auth/login/', {
            'username': 'testartist',
            'password': 'BadPassword',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_unauthenticated_blocked(self):
        # Must return 401 Unauthorized, never 500 crash
        res = self.client.get('/api/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_authenticated_success(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'testartist')

        # Update bio
        patch_res = self.client.patch('/api/auth/profile/', {'bio': 'Music producer from VN'}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Music producer from VN')

    def test_follow_toggle(self):
        target = User.objects.create_user(username='targetuser', password='password123')
        self.client.force_authenticate(user=self.user)

        # Follow
        res1 = self.client.post(f'/api/auth/users/{target.username}/follow/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertTrue(res1.data['following'])

        # Unfollow
        res2 = self.client.post(f'/api/auth/users/{target.username}/follow/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertFalse(res2.data['following'])

