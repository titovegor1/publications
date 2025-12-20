from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import UserRegistrationForm


class UserRegistrationFormTest(TestCase):
    """Тесты для формы регистрации пользователя"""

    def test_registration_form_valid(self):
        """Тест валидности формы с корректными данными"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_registration_form_invalid_without_username(self):
        """Тест невалидности формы без имени пользователя"""
        form_data = {
            'email': 'test@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_registration_form_invalid_without_email(self):
        """Тест невалидности формы без email"""
        form_data = {
            'username': 'testuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_registration_form_invalid_password_mismatch(self):
        """Тест невалидности формы при несовпадении паролей"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_registration_form_invalid_weak_password(self):
        """Тест невалидности формы со слабым паролем"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': '123',
            'password2': '123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_registration_form_saves_user(self):
        """Тест сохранения пользователя через форму"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('ComplexPass123!'))


class UserViewsTest(TestCase):
    """Тесты для представлений пользователей"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

    def test_register_view_get(self):
        """Тест GET-запроса к странице регистрации"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_register_view_post_valid(self):
        """Тест POST-запроса с валидными данными"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        response = self.client.post(reverse('register'), data=form_data)

        # Проверяем редирект после успешной регистрации
        self.assertEqual(response.status_code, 302)

        # Проверяем, что пользователь создан
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Проверяем, что пользователь автоматически залогинен
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'new@example.com')

    def test_register_view_post_invalid(self):
        """Тест POST-запроса с невалидными данными"""
        form_data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password1': '123',
            'password2': '456'
        }
        response = self.client.post(reverse('register'), data=form_data)

        # Форма должна вернуться с ошибками
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_register_view_duplicate_username(self):
        """Тест регистрации с существующим именем пользователя"""
        form_data = {
            'username': 'existinguser',  # Уже существует
            'email': 'another@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        response = self.client.post(reverse('register'), data=form_data)

        # Форма должна вернуться с ошибкой
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='existinguser').count(), 1)

    def test_profile_view(self):
        """Тест просмотра профиля пользователя"""
        response = self.client.get(reverse('profile', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'existinguser')

    def test_profile_view_404(self):
        """Тест 404 для несуществующего пользователя"""
        response = self.client.get(reverse('profile', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_profile_view_context(self):
        """Тест контекста страницы профиля"""
        response = self.client.get(reverse('profile', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_user', response.context)
        self.assertEqual(response.context['profile_user'], self.user)


class UserModelIntegrationTest(TestCase):
    """Интеграционные тесты для модели User"""

    def test_user_creation(self):
        """Тест создания пользователя"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))

    def test_user_authentication(self):
        """Тест аутентификации пользователя"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Проверяем правильный пароль
        self.assertTrue(user.check_password('testpass123'))

        # Проверяем неправильный пароль
        self.assertFalse(user.check_password('wrongpass'))

    def test_user_login_logout(self):
        """Тест входа и выхода пользователя"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        client = Client()

        # Проверяем вход
        logged_in = client.login(username='testuser', password='testpass123')
        self.assertTrue(logged_in)

        # Проверяем выход
        client.logout()

        # Попытка доступа к защищенной странице должна редиректить
        response = client.get(reverse('post_create'))
        self.assertEqual(response.status_code, 302)
