import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateAndEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_pic = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test_pic.gif',
            content=cls.test_pic,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description',
        )
        cls.post = Post.objects.create(
            text='text',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        self.noauth = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_create_post(self):
        """Валидная форма создаст запись в таблице Posts
           и переведёт пользоватлея создавшего запись на
           на страницу его профиля."""
        count_posts = Post.objects.count()
        test_pic = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        create_uploaded = SimpleUploadedFile(
            name='test_pic3.gif',
            content=test_pic,
            content_type='image/gif'
        )
        form_data = {
            'text': 'text22',
            'group': self.group.pk,
            'image': create_uploaded,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.latest('pk')
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.author.username}))
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.image.name, f'posts/{form_data["image"].name}')

    def test_edit_post(self):
        """Валидная форма изменит запись в таблице Posts
           и переведёт пользоватлея создавшего запись на
           на страницу его профиля."""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'text22 new',
            'group': self.group.pk,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data
        )
        update_post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(Post.objects.count(), count_posts)
        self.assertEqual(update_post.text, form_data['text'])
        self.assertEqual(update_post.group.pk, form_data['group'])
        self.assertEqual(update_post.author, self.author)

    def test_create_post_no_auth(self):
        """Проверка что неавторизованный пользователь
            не может создать запись в таблице Posts."""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'text spesh no auth',
            'group': self.group.pk,
        }
        response = self.noauth.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), count_posts)
        last_post = Post.objects.latest('pk')
        self.assertNotEqual(last_post.text, form_data['text'])

    def test_create_comment(self):
        """Валидная форма создаст запись в таблице
           Comments."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий'
        }
        response = self.authorized_client_author.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.latest('pk')
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        ))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.author)

    def test_create_comment_no_auth(self):
        """Проверка что неавторизованный пользователь
            не может создать комментарий к посту."""
        count_comments = Comment.objects.count()
        form_data = {
            'text': 'text'
        }
        self.noauth.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), count_comments)
        self.assertNotEqual(self.post.comments.last(), form_data['text'])
