from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text',
        )

    def test_post_and_group_str(self):
        """Проверка метода __str__ у классов Post и Group."""
        context = (
            (self.post, self.post.text[:15]),
            (self.group, self.group.title)
        )
        for model, exception in context:
            with self.subTest(model=model):
                self.assertEqual(str(model), exception)
