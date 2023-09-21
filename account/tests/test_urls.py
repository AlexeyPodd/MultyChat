from django.test import SimpleTestCase
from django.urls import reverse, resolve

from ..views import UserRegisterView, UserLoginView, logout_user


class TestUrls(SimpleTestCase):
    def test_register_url_resolves(self):
        url = reverse('account:register')
        self.assertEqual(resolve(url).func.view_class, UserRegisterView)

    def test_login_url_resolves(self):
        url = reverse('account:login')
        self.assertEqual(resolve(url).func.view_class, UserLoginView)

    def test_logout_url_resolves(self):
        url = reverse('account:logout')
        self.assertEqual(resolve(url).func, logout_user)
