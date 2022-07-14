from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.no_author = User.objects.create_user(username='no_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.post = Post.objects.create(
            author=PostURLTests.author,
            group=PostURLTests.group,
            text='Тестовый пост',
        )
        cls.authorized_author = Client()
        cls.authorized_author.force_login(PostURLTests.author)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostURLTests.no_author)
        cls.templates_pages_public = {
            '/': 'posts/index.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.author}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.templates_pages_private = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.author}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }

    def test_urls_guest_uses_correct_template(self):
        """URL адрес доступен гостю."""
        for address, template in self.templates_pages_public.items():
            with self.subTest(address=address):
                response = Client().get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_uses_correct_templates(self):
        """URL адрес доступен авторизованому пользователю"""
        for address, template in self.templates_pages_private.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_author_uses_correct_template(self):
        """URL адрес доступен автору поста"""
        test_post = Post.objects.create(
            author=self.author,
            text='Тестовый пост зарегестрированого пользователя'
        )
        address = f'/posts/{test_post.id}/edit/'
        template = 'posts/create_post.html'
        response = self.authorized_author.get(address)
        self.assertTemplateUsed(response, template)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_exists_at_desired_location(self):
        """Проверка несуществующей страницы"""
        response = Client().get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_no_author_of_post_cant_edit_post(self):
        """Страница posts/<post_id>/edit/ не доступна и
        перенаправляет авторизованному пользователю, который не автор поста"""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_post_edit_and_create_url_to_guest_user(self):
        """Страницы /edit/ & /create/ & /comment/
        перенаправляют неавторизованного пользователя"""
        auth_login_edit = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        auth_login_comm = f'/auth/login/?next=/posts/{self.post.id}/comment/'
        redirect_guest_url = {
            f'/posts/{self.post.id}/edit/': auth_login_edit,
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.post.id}/comment/': auth_login_comm
        }
        for adress, redirected in redirect_guest_url.items():
            with self.subTest(adress=adress):
                response = Client().get(adress, follow=True)
                self.assertRedirects(response, redirected)
