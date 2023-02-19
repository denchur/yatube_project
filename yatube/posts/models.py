from django.contrib.auth import get_user_model
from django.db import models
from yatube.settings import MAX_LENGHT_SYMBOLS

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название cообщества"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="Ссылка на группу"
    )
    description = models.TextField(
        verbose_name="Описание группы"
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст поста"
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации"
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
        verbose_name="Сообщество"
    )

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text[0:MAX_LENGHT_SYMBOLS]
