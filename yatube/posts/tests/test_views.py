import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.no_author = User.objects.create_user(username='TestUser')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовый текст',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
            image=cls.uploaded
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostPagesTests.no_author)
        cls.authorized_author = Client()
        cls.authorized_author.force_login(PostPagesTests.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_and_edit_show_correct_context(self):
        """В шаблон /create_post/ передается правильный контекст."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context.get('form')
        if response.context.get('is_edit') is True:
            response = self.authorized_author.get(reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)
        self.assertIsInstance(form, PostForm)

    def context_for_pages_with_paginator(self, page):
        """Контекст для шаблонов index, group_list, profile"""
        pages_reverses = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': self.author}
            )
        }
        response = self.authorized_client.get(pages_reverses[page])
        return response.context['page_obj'][0]

    def test_pages_with_paginator_show_correct_context(self):
        """Шаблоны index, profile, group_list сформированы
        с правильным контекстом."""
        for page in ['index', 'group_list', 'profile']:
            post = self.context_for_pages_with_paginator(page)
            self.assertEqual(post, self.post)
            if page == 'group_list':
                self.assertEqual(
                    post.group.description,
                    self.group.description
                )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        first_object = response.context.get('post')
        post_text_0 = first_object.text
        post_author = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author, self.author)
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_author.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.author,
        )
        response_old = self.authorized_author.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_author.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_follow(self):
        """Проверка возможности подписаться на автора"""
        self.authorized_client.get(reverse(
            'posts:profile_follow', args=[self.author]), follow=True)
        self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow(self):
        """Проверка возможности отписки от автора"""
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', args=[self.author]), follow=True)
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_index(self):
        """Запись появляется в ленте тех, кто подписан на автора
        и не появляется в ленте тех, кто не подписан"""
        # Подписываемся и проверяем созданый пост на странице
        Follow.objects.get_or_create(user=self.no_author, author=self.author)
        new_post = Post.objects.create(
            author=self.author,
            text='Новое тестовое сообщение',
            group=self.group,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(new_post, first_object)
        # Отписываемся и и проверяем страницу
        Follow.objects.filter(user=self.no_author, author=self.author).delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        new_first_object = response.context['page_obj']
        self.assertNotEqual(new_first_object, new_post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.paginator_pages = {
            'posts:index': '',
            'posts:group_list': {'slug': cls.group.slug},
            'posts:profile': {'username': cls.user},
        }
        cls.post = Post.objects.bulk_create([Post(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост'
            + str(i)
        )for i in range(13)])

    def test_first_page_contains_ten_records(self):
        """Тест паджинатора для шаблонов index, group_list, profile"""
        for page_name, kwarg in self.paginator_pages.items():
            with self.subTest(page_name=page_name):
                response = self.client.get(reverse(page_name, kwargs=kwarg))
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Тест 2 страницы паджинатора шаблонов index, group_list, profile"""
        for page_name, kwarg in self.paginator_pages.items():
            with self.subTest(page_name=page_name):
                response = self.client.get(reverse(
                    page_name,
                    kwargs=kwarg) + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
