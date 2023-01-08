from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user_author)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        url_names = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user_author}/',
            f'/posts/{self.post.id}/',
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_anonymous_on_admin_login(self):
        """Страницы по адресу '/create/', '/edit/', '/comment/'
        перенаправит анонимного пользователя на страницу логина.
        """
        redirect_url = 'auth/login/?next='
        login_url = {
            f'/posts/{self.post.id}/edit/':
            f'/{redirect_url}/posts/{self.post.id}/edit/',
            '/create/': f'/{redirect_url}/create/',
            f'/posts/{self.post.id}/comment/':
            f'/{redirect_url}/posts/{self.post.id}/comment/',
        }
        for address, redirect_url in login_url.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_non_author_cannot_edit_post(self):
        """Страница редактирования поста перенаправит НЕавтора
        на страицу поста.
        """
        user = User.objects.create_user(username='non_autor')
        self.authorized_client = Client()
        self.authorized_client.force_login(user)
        address = f'/posts/{self.post.id}/edit/'
        redirect_url = f'/posts/{self.post.id}/'
        response = self.authorized_client.get(address, follow=True)
        self.assertRedirects(response, redirect_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон.
        Страница '/edit/' доступна автору поста.
        """
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user_author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response_author = self.author_client.get(address)
                self.assertTemplateUsed(response_author, template)
                self.assertEqual(response_author.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Запорс к несуществующей странице вернет ошибку 404,
        отдаст кастомный шаблон.
        """
        template = 'core/404.html'
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, template)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
