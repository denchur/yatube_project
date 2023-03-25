from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsUrlTest(TestCase):
    FAKE_POST_ID = 999

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description',
        )
        cls.user = User.objects.create_user(
            'author'
        )
        cls.user2 = User.objects.create_user(
            'noauthor'
        )
        cls.post = Post.objects.create(
            text='text',
            author=PostsUrlTest.user,
            group=PostsUrlTest.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.auth_client_author = Client(username='author')
        self.auth_client_author.force_login(self.user)
        self.authorized_client = Client(username='noauthor')
        self.authorized_client.force_login(self.user2)

    def test_urls_no_auth(self):
        """Тест доступа к urls для неавторизированного пользователя."""
        respone_urls_code = {
            reverse('posts:home_page'): HTTPStatus.OK,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse('posts:group_posts',
                    kwargs={'slug': 'fake-slug'}): HTTPStatus.NOT_FOUND,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): HTTPStatus.OK,
            reverse('posts:post_create'): HTTPStatus.FOUND,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}): HTTPStatus.OK,
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}): HTTPStatus.FOUND,
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.FAKE_POST_ID}): HTTPStatus.NOT_FOUND,
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.FAKE_POST_ID}): HTTPStatus.FOUND,
            reverse('posts:follow_index'): HTTPStatus.FOUND,
        }
        for url, code in respone_urls_code.items():
            with self.subTest(url=url):
                status_code = self.guest_client.get(url).status_code
                self.assertEqual(status_code, code)

    def test_urls_with_auth_and_author(self):
        """Тест доступа к urls для
            авторизированного пользователя являющегося
            автором поста."""
        respone_urls_code = {
            reverse('posts:home_page'): HTTPStatus.OK,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse('posts:group_posts',
                    kwargs={'slug': 'fake-slug'}): HTTPStatus.NOT_FOUND,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): HTTPStatus.OK,
            reverse('posts:post_create'): HTTPStatus.OK,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}): HTTPStatus.OK,
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}): HTTPStatus.OK,
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.FAKE_POST_ID}): HTTPStatus.NOT_FOUND,
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.FAKE_POST_ID}): HTTPStatus.NOT_FOUND,
            reverse('posts:follow_index'): HTTPStatus.OK,
        }
        for url, code in respone_urls_code.items():
            with self.subTest(url=url):
                status_code = self.auth_client_author.get(url).status_code
                self.assertEqual(status_code, code)

    def test_urls_with_auth_no_author(self):
        """Тест доступа к urls для
            авторизированного пользователя не являющегося
            автором поста"""
        respone_urls_code = {
            reverse('posts:home_page'): HTTPStatus.OK,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse('posts:group_posts',
                    kwargs={'slug': 'fake-slug'}): HTTPStatus.NOT_FOUND,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): HTTPStatus.OK,
            reverse('posts:post_create'): HTTPStatus.OK,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}): HTTPStatus.OK,
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}): HTTPStatus.FOUND,
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.FAKE_POST_ID}): HTTPStatus.NOT_FOUND,
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.FAKE_POST_ID}): HTTPStatus.NOT_FOUND,
            reverse('posts:follow_index'): HTTPStatus.OK,
        }
        for url, code in respone_urls_code.items():
            with self.subTest(url=url):
                status_code = self.authorized_client.get(url).status_code
                self.assertEqual(status_code, code)

    def test_urls_redirect_for_guest(self):
        """Тест переадресации для неавторизированного пользователя."""
        urls = {
            reverse('posts:post_create'): '/auth/login/?next=%2Fcreate%2F',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}): (
                '/auth/login/?next=%2Fposts%2F1%2Fedit%2F'),
            reverse('posts:follow_index'): '/auth/login/?next=%2Ffollow%2F'
        }
        for url, redirect in urls.items():
            with self.subTest(url=url):
                respone = self.guest_client.get(url, follow=True)
                self.assertRedirects(respone, redirect)

    def test_urls_redirect_for_auth_no_author(self):
        """Тест переадресацию для авторизированного пользователя не автора."""
        urls = {
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}): (
                reverse('posts:post_detail', kwargs={
                    'post_id': self.post.pk
                }
                )
            ),
        }
        for url, redirect in urls.items():
            with self.subTest(url=url):
                respone = self.authorized_client.get(url, follow=True)
                self.assertRedirects(respone, redirect)
