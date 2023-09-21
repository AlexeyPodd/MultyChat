from django.test import TestCase

from ..forms import RegisterUserForm, LoginUserForm
from ..models import User


class TestRegisterUserForm(TestCase):
    new_user_username = 'new_test_user'
    new_user_password = 'i3oi34mi34iomo34im'
    new_user_email = 'sdkfd@gmail.com'

    def test_valid_data(self):
        data = {
            'username': self.new_user_username,
            'password1': self.new_user_password,
            'password2': self.new_user_password,
            'email': self.new_user_email,
        }
        form = RegisterUserForm(data=data)

        self.assertTrue(form.is_valid())

    def test_no_data(self):
        form = RegisterUserForm(data={})

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)

    def test_not_same_passwords(self):
        data = {
            'username': self.new_user_username,
            'password1': self.new_user_password,
            'password2': self.new_user_password+'123',
            'email': self.new_user_email,
        }
        form = RegisterUserForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)

    def test_user_already_exists(self):
        User.objects.create_user(username=self.new_user_username, email='j'+self.new_user_email,
                                 password='i3oi34mi34g34im')

        data = {
            'username': self.new_user_username,
            'password1': self.new_user_password,
            'password2': self.new_user_password,
            'email': self.new_user_email,
        }
        form = RegisterUserForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)


class TestLoginUserForm(TestCase):
    new_user_username = 'new_test_user'
    new_user_password = 'i3oi34mi34iomo34im'
    new_user_email = 'sdkfd@gmail.com'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username=cls.new_user_username,
            email=cls.new_user_email,
            password=cls.new_user_password,
        )

    def test_valid_data(self):
        data = {
            'username': self.new_user_username,
            'password': self.new_user_password,
        }
        form = LoginUserForm(data=data)

        self.assertTrue(form.is_valid())

    def test_no_data(self):
        formset = LoginUserForm(data={})

        self.assertFalse(formset.is_valid())

    def test_wrong_password(self):
        data = {
            'username': self.new_user_username,
            'password': self.new_user_password + '123',
        }
        form = LoginUserForm(data=data)

        self.assertFalse(form.is_valid())
