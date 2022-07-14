from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Group, Post

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый коммент',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostsModelTest.post
        group = PostsModelTest.group
        comment = PostsModelTest.comment
        expected_object_name_post = post.text
        expected_object_name_group = group.title
        expected_object_name_comment = comment.text
        self.assertEqual(expected_object_name_post, str(post))
        self.assertEqual(expected_object_name_group, str(group))
        self.assertEqual(expected_object_name_comment, str(comment))

    def test_model_post_have_correct_verbose_names(self):
        """Проверка verobose_name модели Post"""
        post = PostsModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_model_post_have_correct_help_texts(self):
        """help_text в модели Post совпадает с ожидаемым."""
        post = PostsModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_model_group__have_correct_verbose_names(self):
        """Проверка verobose_name модели Group"""
        group = PostsModelTest.group
        field_verboses = {
            'title': 'Название группы',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_model_group_have_correct_help_texts(self):
        """help_text в модели Group совпадает с ожидаемым."""
        group = PostsModelTest.group
        field_help_texts = {
            'title': 'Введите название группы',
            'description': 'Введите описание группы',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)
