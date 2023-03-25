import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description',
        )
        cls.user = User.objects.create_user(
            username='author',
        )
        cls.posts_on_first_page = 10
        cls.posts_on_second_page = 3
        Post.objects.bulk_create([Post(title=f'Post {i}')
                                  for i in range(cls.posts_on_first_page
                                                 + cls.posts_on_second_page)])

    def setUp(self):
        self.client = Client()

    def trst_paginator_on_pages(self):
        """Тест пагинатора главное страницыm, страницы постов группы и
            профиль пользователя."""
        url_pages = (
            reverse('posts:home_page'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )
        number_pages = (
            ('?page=1', self.posts_on_first_page),
            ('?page=2', self.posts_on_second_page)
        )
        for reverse_ in url_pages:
            for number_page, count_posts in number_pages:
                with self.subTest(reverse_=reverse_):
                    self.assertEqual(len(self.client.get(
                        reverse_ + number_page).context.get('page_obj')),
                        count_posts
                    )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_pic = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test_pic.gif',
            content=test_pic,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='author')
        cls.suber = User.objects.create_user(username='follower')
        cls.follower = Follow.objects.create(user=cls.suber, author=cls.user)
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description',
        )
        cls.post = Post.objects.create(
            text='text',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='asd',
            post=cls.post,
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.follower_client = Client()
        self.follower_client.force_login(self.suber)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def template_correct_context(self, post):
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)
        self.assertEqual(post.comments.latest('pk'), self.comment)

    def test_pages_uses_correct_template(self):
        """URL адрес использует правильный шаблон."""
        templates_pages_names = {
            reverse('posts:home_page'): 'posts/index.html',
            '/nesushestvuet/': 'core/404.html',
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}): (
                'posts/create_post.html'
            ),
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): (
                        'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}): (
                'posts/post_detail.html'
            ),
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон home_page содержит правильный контекст."""
        respone = self.auth_client.get(reverse('posts:home_page'))
        post = respone.context['page_obj'][0]
        self.template_correct_context(post)

    def test_follow_show_correct_context(self):
        """Шаблон follow_index содержит правильный контекст"""
        respone = self.follower_client.get(reverse('posts:follow_index'))
        post = respone.context['page_obj'][0]
        self.template_correct_context(post)

    def test_group_list_page_show_correct_context(self):
        """Щаблон group_list содержит правильный контекст."""
        slug = reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}
        )
        respone = self.auth_client.get(slug)
        post = respone.context['page_obj'][0]
        self.template_correct_context(post)
        self.assertEqual(respone.context['group'], self.group)

    def test_profile_page_show_correct_context(self):
        """Шааблон profile содержит правильный контекст."""
        url = reverse('posts:profile', kwargs={'username': self.post.author})
        respone = self.auth_client.get(url)
        post = respone.context['page_obj'][0]
        self.template_correct_context(post)
        self.assertEqual(respone.context['username'], self.user)
        self.assertFalse(respone.context['following'])

    def test_post_detail_pages_show_correct_context(self):
        """Шааблон post_detail содержит правильный контекст."""
        slug = reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        form_fields = {
            'text': forms.fields.CharField
        }
        respone = self.auth_client.get(slug)
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = respone.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
        post = respone.context['post']
        self.template_correct_context(post)
        com = respone.context['comments'][0]
        self.assertEqual(com, self.comment)

    def test_create_post_edit_show_correct_context(self):
        """Шаблон post_create при редактировании
            поста содержит правильный контекст."""
        slug = reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        response = self.auth_client.get(slug)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        """Шаблон post_create при создании поста
             содержит правильный контекст."""
        slug = reverse('posts:post_create')
        response = self.auth_client.get(slug)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_on_home_page_and_group_and_profile(self):
        """Созданный пост отображается
            на главной странице, странице группы к которой он предназначенн
            и профиле пользоватлея создавшего пост."""
        slugs = (
            reverse('posts:home_page'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ),
        )
        for slug in slugs:
            response = self.auth_client.get(slug)
            self.assertIn(self.post, response.context['page_obj'].object_list)

    def test_post_not_another_group(self):
        """Созданный пост не отображается в
            группе которой не предназначен."""
        new_group = Group.objects.create(
            title='new title',
            slug='new-slug',
            description='description',
        )
        response = self.auth_client.get(
            reverse('posts:group_posts', kwargs={'slug': new_group.slug})
        )
        self.assertNotIn(self.post, response.context['page_obj'].object_list)

    def test_cache(self):
        """Тест кеша главной страницы"""
        new_post = Post.objects.create(
            text='new-text',
            author=self.user
        )
        respone = self.auth_client.get(reverse('posts:home_page'))
        post_on_page = respone.context['page_obj']
        self.assertIn(new_post, post_on_page)
        new_post.delete()
        response_2 = self.auth_client.get(reverse('posts:home_page'))
        self.assertEqual(respone.content, response_2.content)
        cache.clear()
        response_3 = self.auth_client.get(reverse('posts:home_page'))
        self.assertNotEqual(respone.content, response_3.content)


class FollowingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create(username='user')
        cls.author = User.objects.create(username='author')
        cls.post = Post.objects.create(
            text='post',
            author=cls.author,
        )

    def setUp(self):
        self.user_session = Client()
        self.author_session = Client()
        self.user_session.force_login(self.follower)
        self.author_session.force_login(self.author)

    def test_see_follower_post(self):
        """У подписавшегося клиента отображаются посты
            на странице follow_index"""
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        respone = self.user_session.get(reverse('posts:follow_index'))
        self.assertIn(self.post, respone.context['page_obj'])

    def test_see_unfollow_post(self):
        respone = self.author_session.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post,
                         respone.context['page_obj'])

    def test_follow(self):
        """Авторизированный юзер может подписаться"""
        count = Follow.objects.count()
        self.user_session.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        follow = Follow.objects.latest('pk')
        self.assertEqual(self.follower, follow.user)
        self.assertEqual(self.author, follow.author)
        self.assertEqual(Follow.objects.count(), count + 1)

    def test_unfollow(self):
        """Подписаннай и авторизированный пользователь
            может отписаться."""
        Follow.objects.create(
            user=self.follower,
            author=self.author,
        )
        count = Follow.objects.count()
        self.user_session.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author}))
        self.assertEqual(Follow.objects.count(), count - 1)

    def test_two_follow_on_author(self):
        count = Follow.objects.count()
        self.user_session.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.user_session.get(
            reverse('posts:profile_follow', kwargs={'username': self.author}))
        self.assertEqual(Follow.objects.count(), count + 1)
