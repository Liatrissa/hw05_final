import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(
            username='post_author',
        )
        cls.another_user = User.objects.create_user(username='noname')
        cls.comm_author = User.objects.create_user(
            username='comm_author')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.edited_group = Group.objects.create(
            title='Название группы после редактирования',
            slug='test-edited',
            description='Тестовое описание группы после редактирования'
        )
        cls.post = Post.objects.create(
            author=cls.post_author,
            text='Тестовый текст для поста',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.post_author)
        self.auth_user_comm = Client()
        self.auth_user_comm.force_login(self.comm_author)

    def test_authorized_user_create_post(self):
        """Проверка создания записи авторизированным пользователем"""
        posts_count = Post.objects.count()
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
            'text': 'Текст поста',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.post_author.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post_author)
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.image.name, 'posts/small.gif')

    def test_no_create_post(self):
        """Проверка запрета добавления поста в базу данных
           неавторизованым пользователем"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Текст поста',
                     'group': self.group.id}
        response = self.guest_user.post(reverse('posts:post_create'),
                                        data=form_data,
                                        follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        error = 'Поcт добавлен в базу данных по ошибке'
        self.assertNotEqual(Post.objects.count(),
                            posts_count + 1,
                            error)

    def test_authorized_user_edit_post(self):
        """Проверка редактирования записи авторизированным пользователем"""
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id
        }
        response = self.authorized_user.post(
            reverse(
                'posts:post_edit',
                args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post_author)
        self.assertEqual(post.group_id, form_data['group'])

    def test_no_edit_post(self):
        """Проверка запрета редактирования неавторизованным пользователем"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Отредактированный текст поста',
                     'group': self.edited_group.id
                     }
        response = self.guest_user.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        error = 'Поcт добавлен в базу данных ошибочно'
        self.assertNotEqual(Post.objects.count(),
                            posts_count + 1,
                            error)
        edited_post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(edited_post.text, form_data['text'])
        self.assertNotEqual(edited_post.group.id, form_data['group'])

    def test_authorized_user_create_comment(self):
        """Проверка создания комментария авторизированным клиентом."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый коментарий'}
        response = self.auth_user_comm.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        comment = Comment.objects.latest('id')
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.comm_author)
        self.assertEqual(comment.post_id, self.post.id)
        self.assertRedirects(
            response, reverse('posts:post_detail', args={self.post.id}))

    def test_nonauthorized_user_create_comment(self):
        """Проверка создания комментария не авторизированным пользователем."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый коментарий'}
        response = self.guest_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        redirect = reverse('login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(response, redirect)
