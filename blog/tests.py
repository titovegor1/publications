from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Post, Category
from .managers import get_published_posts
from .forms import PostForm, CategoryForm


class CategoryModelTest(TestCase):
    """Тесты для модели Category"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            title='Test Category',
            description='Test Description',
            author=self.user
        )

    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.category.title, 'Test Category')
        self.assertEqual(self.category.description, 'Test Description')
        self.assertEqual(self.category.author, self.user)

    def test_category_str(self):
        """Тест строкового представления категории"""
        self.assertEqual(str(self.category), 'Test Category')

    def test_category_without_author(self):
        """Тест создания категории без автора"""
        category = Category.objects.create(
            title='No Author Category',
            description='Test'
        )
        self.assertIsNone(category.author)

    def test_category_cascade_delete(self):
        """Тест каскадного удаления при удалении пользователя"""
        category_id = self.category.id
        self.user.delete()
        self.assertFalse(Category.objects.filter(id=category_id).exists())


class PostModelTest(TestCase):
    """Тесты для модели Post"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            title='Test Category',
            description='Test Description'
        )
        self.post = Post.objects.create(
            title='Test Post',
            text='Test Content',
            author=self.user
        )

    def test_post_creation(self):
        """Тест создания поста"""
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.text, 'Test Content')
        self.assertEqual(self.post.author, self.user)
        self.assertIsNotNone(self.post.pub_date)

    def test_post_str(self):
        """Тест строкового представления поста"""
        self.assertEqual(str(self.post), 'Test Post')

    def test_post_pub_date_auto_now_add(self):
        """Тест автоматической установки даты публикации"""
        self.assertIsNotNone(self.post.pub_date)
        self.assertLessEqual(self.post.pub_date, timezone.now())

    def test_post_categories_many_to_many(self):
        """Тест связи ManyToMany с категориями"""
        self.post.categories.add(self.category)
        self.assertEqual(self.post.categories.count(), 1)
        self.assertIn(self.category, self.post.categories.all())

    def test_post_cascade_delete_author(self):
        """Тест каскадного удаления при удалении автора"""
        post_id = self.post.id
        self.user.delete()
        self.assertFalse(Post.objects.filter(id=post_id).exists())

    def test_post_multiple_categories(self):
        """Тест добавления нескольких категорий к посту"""
        category2 = Category.objects.create(
            title='Category 2',
            description='Description 2'
        )
        self.post.categories.add(self.category, category2)
        self.assertEqual(self.post.categories.count(), 2)


class GetPublishedPostsTest(TestCase):
    """Тесты для функции get_published_posts()"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_get_published_posts_default(self):
        """Тест получения опубликованных постов (все посты по умолчанию)"""
        post = Post.objects.create(
            title='Published Post',
            text='Content',
            author=self.user
        )
        published = get_published_posts()
        self.assertIn(post, published)

    def test_get_published_posts_uses_current_time(self):
        """Тест использования текущего времени (не константы)"""
        # Создаем пост с текущей датой
        post = Post.objects.create(
            title='Current Post',
            text='Content',
            author=self.user
        )
        # Проверяем, что пост опубликован
        published = get_published_posts()
        self.assertIn(post, published)

    def test_get_published_posts_with_custom_queryset(self):
        """Тест функции с пользовательским QuerySet"""
        post1 = Post.objects.create(
            title='Post 1',
            text='Content 1',
            author=self.user
        )
        post2 = Post.objects.create(
            title='Post 2',
            text='Content 2',
            author=self.user
        )

        # Передаем кастомный queryset
        custom_queryset = Post.objects.filter(title='Post 1')
        published = get_published_posts(custom_queryset)

        self.assertEqual(published.count(), 1)
        self.assertIn(post1, published)
        self.assertNotIn(post2, published)

    def test_get_published_posts_filters_future_posts(self):
        """Тест фильтрации постов с будущей датой"""
        # Создаем пост с датой в прошлом (опубликованный)
        past_post = Post.objects.create(
            title='Past Post',
            text='Content',
            author=self.user
        )
        past_post.pub_date = timezone.now() - timedelta(days=1)
        past_post.save()

        # Создаем пост с датой в будущем (неопубликованный)
        future_post = Post.objects.create(
            title='Future Post',
            text='Content',
            author=self.user
        )
        future_post.pub_date = timezone.now() + timedelta(days=1)
        future_post.save()

        published = get_published_posts()

        self.assertIn(past_post, published)
        self.assertNotIn(future_post, published)


class PostFormTest(TestCase):
    """Тесты для формы PostForm"""

    def setUp(self):
        self.category = Category.objects.create(
            title='Test Category',
            description='Test Description'
        )

    def test_post_form_valid(self):
        """Тест валидности формы с корректными данными"""
        form_data = {
            'title': 'Test Post',
            'text': 'Test Content',
            'categories': [self.category.id]
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_post_form_without_categories(self):
        """Тест формы без категорий (необязательное поле)"""
        form_data = {
            'title': 'Test Post',
            'text': 'Test Content',
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_post_form_invalid_without_title(self):
        """Тест невалидности формы без заголовка"""
        form_data = {
            'text': 'Test Content',
        }
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_post_form_invalid_without_text(self):
        """Тест невалидности формы без текста"""
        form_data = {
            'title': 'Test Post',
        }
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)


class CategoryFormTest(TestCase):
    """Тесты для формы CategoryForm"""

    def test_category_form_valid(self):
        """Тест валидности формы с корректными данными"""
        form_data = {
            'title': 'Test Category',
            'description': 'Test Description'
        }
        form = CategoryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_category_form_invalid_without_title(self):
        """Тест невалидности формы без заголовка"""
        form_data = {
            'description': 'Test Description'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_category_form_invalid_without_description(self):
        """Тест невалидности формы без описания"""
        form_data = {
            'title': 'Test Category'
        }
        form = CategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)


class PostViewsTest(TestCase):
    """Тесты для представлений постов"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            title='Test Category',
            description='Test Description'
        )
        self.post = Post.objects.create(
            title='Test Post',
            text='Test Content',
            author=self.user
        )
        self.post.categories.add(self.category)

    def test_index_view_get(self):
        """Тест GET-запроса к главной странице"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_index_view_pagination(self):
        """Тест пагинации на главной странице"""
        # Создаем 15 постов
        for i in range(15):
            Post.objects.create(
                title=f'Post {i}',
                text=f'Content {i}',
                author=self.user
            )

        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        # По умолчанию 10 постов на странице
        self.assertTrue('page_obj' in response.context)

    def test_post_detail_view(self):
        """Тест детального просмотра поста"""
        response = self.client.get(reverse('post_detail', args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertContains(response, 'Test Content')

    def test_post_detail_view_404(self):
        """Тест 404 для несуществующего поста"""
        response = self.client.get(reverse('post_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_category_posts_view(self):
        """Тест просмотра постов категории"""
        response = self.client.get(reverse('category_posts', args=[self.category.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertContains(response, 'Test Category')

    def test_category_posts_view_404(self):
        """Тест 404 для несуществующей категории"""
        response = self.client.get(reverse('category_posts', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_user_posts_view(self):
        """Тест просмотра постов пользователя"""
        response = self.client.get(reverse('user_posts', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_user_posts_view_404(self):
        """Тест 404 для несуществующего пользователя"""
        response = self.client.get(reverse('user_posts', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_post_create_view_requires_login(self):
        """Тест требования авторизации для создания поста"""
        response = self.client.get(reverse('post_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_post_create_view_authenticated(self):
        """Тест создания поста авторизованным пользователем"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('post_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_post_create_view_post(self):
        """Тест POST-запроса для создания поста"""
        self.client.login(username='testuser', password='testpass123')
        post_data = {
            'title': 'New Post',
            'text': 'New Content',
            'categories': [self.category.id]
        }
        response = self.client.post(reverse('post_create'), data=post_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Post.objects.filter(title='New Post').exists())

    def test_search_view_with_query(self):
        """Тест поиска с запросом"""
        response = self.client.get(reverse('search'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_search_view_without_query(self):
        """Тест поиска без запроса"""
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)

    def test_search_view_no_results(self):
        """Тест поиска без результатов"""
        response = self.client.get(reverse('search'), {'q': 'NonExistent'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test Post')

    def test_category_create_view_requires_login(self):
        """Тест требования авторизации для создания категории"""
        response = self.client.get(reverse('category_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_category_create_view_authenticated(self):
        """Тест создания категории авторизованным пользователем"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('category_create'))
        self.assertEqual(response.status_code, 200)

    def test_category_create_view_post(self):
        """Тест POST-запроса для создания категории"""
        self.client.login(username='testuser', password='testpass123')
        category_data = {
            'title': 'New Category',
            'description': 'New Description'
        }
        response = self.client.post(reverse('category_create'), data=category_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Category.objects.filter(title='New Category').exists())
