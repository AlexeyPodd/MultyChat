from django.contrib import auth
from django.test import TestCase, Client
from django.urls import reverse

from ..models import User


class TestView(TestCase):
    """
    Base Class for testing
    """
    url_name = ''
    dummy_username = 'new_test_user'
    dummy_password = 'i3oi34mi34iomo34im'
    dummy_email = 'sdkfd@gmail.com'

    def setUp(self):
        self.client = Client()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse(viewname=cls.url_name)


class TestUserRegisterView(TestView):
    url_name = 'account:register'

    def test_GET(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/form.html')

    def test_POST_registering(self):
        users_amount = User.objects.count()

        response = self.client.post(
            self.url,
            {
                'username': self.dummy_username,
                'password1': self.dummy_password,
                'password2': self.dummy_password,
                'email': self.dummy_email,
            },
        )

        self.assertEqual(User.objects.count(), users_amount+1)

        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        self.assertRedirects(response, reverse('chat:home'))

    def test_POST_same_username(self):
        User.objects.create_user(username=self.dummy_username, password='1234567', email='sdkdofg@gmail.com')
        users_amount = User.objects.count()

        response = self.client.post(
            self.url,
            {
                'username': self.dummy_username,
                'password1': self.dummy_password,
                'password2': self.dummy_password,
                'email': self.dummy_email,
            },
        )

        self.assertEqual(User.objects.count(), users_amount)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/form.html')


class TestUserLoginView(TestView):
    url_name = 'account:login'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(
            username=cls.dummy_username,
            password=cls.dummy_password,
            email=cls.dummy_email,
        )

    def test_GET(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/form.html')

    def test_POST_authorises(self):
        response = self.client.post(self.url, {'username': self.dummy_username, 'password': self.dummy_password})

        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        self.assertRedirects(response, reverse('chat:home'))

    def test_POST_redirects_to_next(self):
        next_page_url = reverse('chat:banned-list')
        response = self.client.post(
            self.url + '?next=' + next_page_url,
            {'username': self.dummy_username, 'password': self.dummy_password}
        )

        self.assertRedirects(response, next_page_url)

    def test_POST_not_authorises_wrong_password(self):
        response = self.client.post(self.url, {'username': self.dummy_username, 'password': self.dummy_password+'123'})

        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/form.html')


class TestLogoutUser(TestView):
    url_name = 'account:logout'

    def test_GET_logout_user_and_redirects(self):
        self.user = User.objects.create_user(
            username=self.dummy_username,
            password=self.dummy_password,
            email=self.dummy_email,
        )
        self.client.login(username=self.dummy_username, password=self.dummy_password)

        response = self.client.get(self.url)

        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)
        self.assertRedirects(response, reverse('chat:home'))
