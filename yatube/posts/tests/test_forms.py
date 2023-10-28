import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_client_cannot_create_post(self):
        """Неавторизованный пользователь не может создать запись в Post."""
        guest_client = Client()
        redirect_url = '/auth/login/?next=/create/'
        form_data = {
            'text': 'Тестовый пост',
            'author': self.user,
            'group': self.group.id,
        }
        response = guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Post.objects.count(), 0)

    def test_post_create(self):
        """Валидная форма создает запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'author': self.user,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post_first = Post.objects.first()
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post_first.text, form_data['text'])
        self.assertEqual(post_first.author, self.user)
        self.assertEqual(post_first.group, self.group)
        self.assertEqual(post_first.image, 'posts/small.gif')

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""
        group_new = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug_2',
            description='Тестовое описание 2',
        )
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=group_new,
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост отредактированный',
            'group': group_new.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        post_first = Post.objects.first()
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post_first.text, form_data['text'])
        self.assertEqual(post_first.author, self.user)
        self.assertEqual(post_first.group, group_new)

    def test_comment_create(self):
        """Валидная форма создает комментарий к записи в Post."""
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'Тестовый комментарий',
            'author': self.user,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        comment_first = Comment.objects.first()
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': post.id})
        )
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment_first.text, form_data['text'])

    def test_anonymus_user_cannot_creat_comment(self):
        """Неавторизованный пользователь не может оставить комментарий."""
        guest_client = Client()
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'Тестовый комментарий',
            'author': self.user,
        }
        redirect_url = f'/auth/login/?next=/posts/{post.id}/comment/'
        response = guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Comment.objects.count(), 0)
