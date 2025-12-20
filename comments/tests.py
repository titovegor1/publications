from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from blog.models import Post
from .models import Comment
from .forms import CommentForm


class CommentModelTest(TestCase):
    """Тесты для модели Comment"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            text='Test Content',
            author=self.user
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            text='Test Comment'
        )

    def test_comment_creation(self):
        """Тест создания комментария"""
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.text, 'Test Comment')
        self.assertIsNotNone(self.comment.created_at)

    def test_comment_str(self):
        """Тест строкового представления комментария"""
        expected_str = f'Comment by {self.user.username} on {self.post.title}'
        self.assertEqual(str(self.comment), expected_str)

    def test_comment_created_at_auto_now_add(self):
        """Тест автоматической установки времени создания"""
        self.assertIsNotNone(self.comment.created_at)

    def test_comment_cascade_delete_post(self):
        """Тест каскадного удаления при удалении поста"""
        comment_id = self.comment.id
        self.post.delete()
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_comment_cascade_delete_user(self):
        """Тест каскадного удаления при удалении пользователя"""
        comment_id = self.comment.id
        self.user.delete()
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_comment_related_name(self):
        """Тест обратной связи через related_name"""
        comments = self.post.comments.all()
        self.assertIn(self.comment, comments)
        self.assertEqual(comments.count(), 1)

    def test_multiple_comments_on_post(self):
        """Тест множественных комментариев к одному посту"""
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        comment2 = Comment.objects.create(
            post=self.post,
            user=user2,
            text='Second Comment'
        )

        comments = self.post.comments.all()
        self.assertEqual(comments.count(), 2)
        self.assertIn(self.comment, comments)
        self.assertIn(comment2, comments)


class CommentFormTest(TestCase):
    """Тесты для формы комментария"""

    def test_comment_form_valid(self):
        """Тест валидности формы с корректными данными"""
        form_data = {
            'text': 'Test Comment Text'
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid_without_text(self):
        """Тест невалидности формы без текста"""
        form_data = {}
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_comment_form_empty_text(self):
        """Тест невалидности формы с пустым текстом"""
        form_data = {
            'text': ''
        }
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_comment_form_fields(self):
        """Тест наличия только необходимых полей в форме"""
        form = CommentForm()
        self.assertEqual(list(form.fields.keys()), ['text'])


class CommentViewsTest(TestCase):
    """Тесты для представлений комментариев"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            text='Test Content',
            author=self.user
        )

    def test_add_comment_requires_login(self):
        """Тест требования авторизации для добавления комментария"""
        response = self.client.post(
            reverse('add_comment', args=[self.post.pk]),
            data={'text': 'Test Comment'}
        )
        # Должен быть редирект на страницу логина
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.exists())

    def test_add_comment_authenticated_valid(self):
        """Тест добавления комментария авторизованным пользователем"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('add_comment', args=[self.post.pk]),
            data={'text': 'Test Comment'}
        )

        # Проверяем редирект обратно к посту
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('post_detail', args=[self.post.pk]))

        # Проверяем, что комментарий создан
        self.assertTrue(Comment.objects.filter(text='Test Comment').exists())
        comment = Comment.objects.get(text='Test Comment')
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.user, self.user)

    def test_add_comment_to_nonexistent_post(self):
        """Тест добавления комментария к несуществующему посту"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('add_comment', args=[9999]),
            data={'text': 'Test Comment'}
        )
        self.assertEqual(response.status_code, 404)

    def test_add_comment_invalid_form(self):
        """Тест добавления комментария с невалидной формой"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('add_comment', args=[self.post.pk]),
            data={'text': ''}  # Пустой текст
        )

        # Должен быть редирект обратно к посту даже при невалидной форме
        self.assertEqual(response.status_code, 302)
        # Комментарий не должен быть создан
        self.assertFalse(Comment.objects.exists())

    def test_add_comment_get_request(self):
        """Тест GET-запроса к представлению добавления комментария"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('add_comment', args=[self.post.pk]))

        # Должен быть редирект обратно к посту
        self.assertEqual(response.status_code, 302)
        # Комментарий не должен быть создан
        self.assertFalse(Comment.objects.exists())

    def test_comment_appears_on_post_detail(self):
        """Тест отображения комментария на странице поста"""
        comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            text='Test Comment'
        )

        response = self.client.get(reverse('post_detail', args=[self.post.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Comment')
        self.assertContains(response, self.user.username)


class CommentIntegrationTest(TestCase):
    """Интеграционные тесты для комментариев"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            text='Test Content',
            author=self.user1
        )

    def test_multiple_users_commenting(self):
        """Тест комментирования несколькими пользователями"""
        # Первый пользователь добавляет комментарий
        self.client.login(username='user1', password='testpass123')
        self.client.post(
            reverse('add_comment', args=[self.post.pk]),
            data={'text': 'Comment from user1'}
        )

        # Второй пользователь добавляет комментарий
        self.client.logout()
        self.client.login(username='user2', password='testpass123')
        self.client.post(
            reverse('add_comment', args=[self.post.pk]),
            data={'text': 'Comment from user2'}
        )

        # Проверяем, что оба комментария созданы
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(self.post.comments.count(), 2)

        # Проверяем авторов комментариев
        comments = Comment.objects.all()
        users = [comment.user for comment in comments]
        self.assertIn(self.user1, users)
        self.assertIn(self.user2, users)

    def test_comment_ordering(self):
        """Тест порядка комментариев"""
        # Создаем несколько комментариев
        comment1 = Comment.objects.create(
            post=self.post,
            user=self.user1,
            text='First Comment'
        )
        comment2 = Comment.objects.create(
            post=self.post,
            user=self.user2,
            text='Second Comment'
        )
        comment3 = Comment.objects.create(
            post=self.post,
            user=self.user1,
            text='Third Comment'
        )

        comments = self.post.comments.all()
        self.assertEqual(comments.count(), 3)

        # Проверяем, что все комментарии есть
        self.assertIn(comment1, comments)
        self.assertIn(comment2, comments)
        self.assertIn(comment3, comments)
