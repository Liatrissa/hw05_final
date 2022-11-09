from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест поста')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_unauthorized_user_urls_status_code(self):
        """Проверка доступа для неавторизованного пользователя."""
        pages = ('/',
                 f'/group/{self.group.slug}/',
                 f'/profile/{self.user.username}/',
                 f'/posts/{self.post.id}/')
        for page in pages:
            response = self.guest_client.get(page)
            error = f'Ошибка: нет доступа до страницы {page}'
            self.assertEqual(response.status_code, HTTPStatus.OK, error)

    def test_urls_redirect_guest_client(self):
        """Редирект неавторизованного пользователя"""
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        pages = {'/create/': url1,
                 f'/posts/{self.post.id}/edit/': url2,
                 }
        for page, template in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, template)

    def test_authorized_user_urls_status_code(self):
        """Проверка доступа для авторизованного пользователя."""
        pages = ('/create/',
                 f'/posts/{self.post.id}/edit/')
        for page in pages:
            response = self.authorized_client.get(page)
            error = f'Ошибка: нет доступа до страницы {page}'
            self.assertEqual(response.status_code, HTTPStatus.OK, error)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                error = f'Ошибка: {url} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error)

    def test_404(self):
        """Запрос несуществующей страницы"""
        response = self.guest_client.get('/test')
        error = 'Ошибка: unexisting_url не работает'
        self.assertEquals(response.status_code,
                          HTTPStatus.NOT_FOUND,
                          error)
        self.assertTemplateUsed(response, 'core/404.html')
