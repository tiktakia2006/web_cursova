from django.test import TestCase
from network.models import Post, Profile, Comment, Route, CustomUser, FriendRequest
from django.core.files.uploadedfile import SimpleUploadedFile
from network.forms import CommentForm, PostForm, RouteForm, SettingsForm, User
from network.models import CustomUser, Profile, Post
from django.urls import reverse
from unittest.mock import patch
from django.contrib.auth import get_user_model

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='pass')
        self.profile = Profile.objects.create(user=self.user)
        self.post = Post.objects.create(user=self.user, caption='Test caption')
        self.route = Route.objects.create(
            user=self.user,
            start_location='A',
            end_location='B',
            description='Some description'
        )

    def test_post_str(self):
        self.assertEqual(str(self.post), 'Test caption')

    def test_route_str(self):
        self.assertEqual(str(self.route), 'A - B')

    def test_comment_creation(self):
        comment = Comment.objects.create(user=self.user, post=self.post, content='Nice one!')
        self.assertEqual(str(comment), f"{self.user.username} - {self.post.caption}")


class FormTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='pass')
        self.profile = Profile.objects.create(user=self.user)

    def test_comment_form_valid(self):
        form = CommentForm(data={'content': 'Test comment'})
        self.assertTrue(form.is_valid())

    def test_post_form(self):
        form = PostForm(data={'caption': 'Some text'})
        self.assertTrue(form.is_valid())

    def test_settings_password_mismatch(self):
        form = SettingsForm(data={
            'email': 'test@test.com',
            'password1': '123',
            'password2': '456'
        })
        self.assertFalse(form.is_valid())

class ViewTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='admin', password='pass', is_staff=True, is_superuser=True)
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()
        self.admin_user.save()

        self.normal_user = User.objects.create_user(username='user', password='pass')
        self.other_user = User.objects.create_user(username='other', password='pass')

        self.post = Post.objects.create(user=self.normal_user, caption='Test post')
        self.route = Route.objects.create(user=self.normal_user, start_location='A', end_location='B',
                                          description='Desc')

    def test_login_view(self):
        User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',

        })
        self.assertEqual(response.status_code, 302)

    @patch('captcha.fields.client.submit')
    def test_registration(self, mock_submit):
        mock_submit.return_value.is_valid = True

        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'Testpass123!',
            'password2': 'Testpass123!',
            'g-recaptcha-response': 'PASSED',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_protected_page_redirect(self):
        response = self.client.get(reverse('create_post'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_protected_page_authenticated(self):
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('create_post'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_view_post(self):
        self.client.login(username='user', password='pass')
        response = self.client.post(reverse('create_post'), {
            'caption': 'New post test'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(caption='New post test').exists())

    def test_accept_and_remove_friend(self):
        FriendRequest.objects.create(from_user=self.other_user, to_user=self.normal_user)
        self.client.login(username='user', password='pass')
        response = self.client.post(reverse('accept_friend', args=[self.other_user.id]))
        self.assertRedirects(response, reverse('friends'))
        profile = Profile.objects.get(user=self.normal_user)
        self.assertIn(self.other_user, profile.friends.all())
        response = self.client.post(reverse('remove_friend', args=[self.other_user.id]))
        self.assertRedirects(response, reverse('friends'))
        profile.refresh_from_db()
        self.assertNotIn(self.other_user, profile.friends.all())

    def test_like_post_toggle(self):
        self.client.login(username='user', password='pass')
        self.assertNotIn(self.normal_user, self.post.likes.all())
        response = self.client.post(reverse('like_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.normal_user, Post.objects.get(pk=self.post.pk).likes.all())
        response = self.client.post(reverse('like_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.normal_user, Post.objects.get(pk=self.post.pk).likes.all())




