from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый текст ',
            author=cls.user,
        )

    def test_post_str(self):
        """Проверяем, что у моделей корректно работает __str__."""
        error = f"Вывод не имеет {settings.LEN_OF_POST} символов"
        self.assertEqual(self.post.__str__(),
                         self.post.text[:settings.LEN_OF_POST],
                         error)

    def test_post_verbose_name(self):
        """Проверка verbose_name у post."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации поста',
            'author': 'Автор поста',
            'group': 'Группа', }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                error = f'Поле {value} ожидало значение {expected}'
                verbose_name = self.post._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected, error)

    def test_post_help_text(self):
        """Проверка help_text у post."""
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост', }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                error = f'Поле {value} ожидало значение {expected}'
                help_text = self.post._meta.get_field(value).help_text
                self.assertEqual(help_text, expected, error)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_str(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.group.title, str(self.group))

    def test_group_verbose_name(self):
        """Проверка verbose_name у group."""
        field_verboses = {
            'title': 'Название группы',
            'slug': 'Уникальный адрес группы',
            'description': 'Описание сообществ',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                error = f'Поле {value} ожидало значение {expected}'
                verbose_name = self.group._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected, error)
