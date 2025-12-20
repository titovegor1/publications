from django.db import models
from django.utils import timezone


def get_published_posts(queryset=None):
    """
    Возвращает QuerySet опубликованных постов.

    Пост считается опубликованным, если он существует (все посты опубликованы по умолчанию).
    Использует timezone.now() для обеспечения вычисления текущей даты/времени при каждом запросе.

    Аргументы:
        queryset: Опциональный базовый QuerySet для фильтрации. Если None, использует Post.objects.all()

    Возвращает:
        QuerySet опубликованных объектов Post
    """
    if queryset is None:
        from blog.models import Post
        queryset = Post.objects.all()

    current_time = timezone.now()

    return queryset.filter(pub_date__lte=current_time)
