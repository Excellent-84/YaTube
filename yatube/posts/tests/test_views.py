import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from http import HTTPStatus

from ..models import Follow, Group, Post
from ..forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def check_post_object(self, post):
        """Избегаем дублирования тестов."""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)
            self.assertEqual(post.image, self.post.image)

    def test_index_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_post_object(response.context['page_obj'][0])

    def test_group_list_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_post_object(response.context['page_obj'][0])

    def test_profile_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(response.context['author'], self.user)
        self.check_post_object(response.context['page_obj'][0])

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.check_post_object(response.context['post'])

    def test_post_create_show_correct_context(self):
        """Шаблоны post_create, post_edit сформированы
        с правильным контекстом.
        """
        urls = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        }
        for value in urls:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form = response.context.get('form')
                self.assertIsInstance(form, PostForm)
                is_edit_value = bool(value == reverse(
                    'posts:post_edit', kwargs={'post_id': self.post.id})
                )
                self.assertEqual(
                    response.context.get('is_edit'), is_edit_value
                )

    def test_post_was_not_included_another_group(self):
        """Проверяем, что созданный пост не попал в другую группу"""
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug_2',
            description='Тестовое описание 2',
        )
        Post.objects.create(
            text='Тестовый пост 2',
            author=self.user,
            group=self.group,
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': new_group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_paginate_page(self):
        """Проверка паджинатора страниц."""
        Post.objects.bulk_create(
            [Post(
                text=f'Пост {index}',
                author=self.user,
                group=self.group)
                for index in range(1, 13)]
        )
        paginator_amount = 10
        second_page_amount = 3
        reverse_pages = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        }
        pages = [
            (1, paginator_amount),
            (2, second_page_amount),
        ]
        for url in reverse_pages:
            for page, count in pages:
                with self.subTest(url=url):
                    response = self.authorized_client.get(url, {'page': page})
                    self.assertEqual(len(response.context['page_obj']), count)

    def test_check_cache(self):
        """Проверка работы кэша."""
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.first().delete()
        response_second = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_second.content)
        cache.clear()
        response_third = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_third.content)

    def test_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        author_follow = User.objects.create_user(username='author_follow')
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': author_follow.username})
        )
        self.assertEqual(Follow.objects.count(), 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=author_follow
        ).exists())
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': author_follow.username})
        )
        self.assertEqual(Follow.objects.count(), 0)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=author_follow
        ).exists())

    def test_new_posts_in_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.
        """
        author_follow = User.objects.create_user(username='Подписан')
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': author_follow.username})
        )
        author_unfollow = User.objects.create_user(username='НЕ_подписан')
        author_unfollow_client = Client()
        author_unfollow_client.force_login(author_unfollow)
        new_post = Post.objects.create(
            text='Тестовый пост подписки',
            author=author_follow,
            group=self.group
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0], new_post)
        response = author_unfollow_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
