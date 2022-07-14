import shutil
import tempfile
from xml.etree.ElementTree import Comment

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
        )
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def image_create(self):
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.get_small_gif(),
            content_type='image/gif'
        )
        return uploaded

    def get_small_gif(self):
        return (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    def test_create_post_form(self):
        """Валидная форма create_post создает запись."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост1',
            'group': self.group.id,
            'image': self.image_create(),
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.all()[0]
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.author}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.image.read(), self.get_small_gif())

    def test_post_edit_form(self):
        """Валидная форма post_edit редактирует запись."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый edit пост',
            'group': self.group.id,
            'image': self.image_create(),
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post = Post.objects.all()[0]
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.image.read(), self.get_small_gif())

    def test_add_comment_form(self):
        """Валидная форма add_comment создает комментарий"""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый коммент'}
        response = self.authorized_author.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        comments = Comment.objects.all()[0]
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comments.text, form_data['text'])
