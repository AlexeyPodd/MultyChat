from django.test import TestCase, Client
from django.urls import reverse

from account.models import User


class TestView(TestCase):
    """
    Base Class for testing
    """
    url_name = ''
    url_kwargs = {}

    dummy_username = 'dummy_test_user'
    dummy_password = '32145'
    dummy_email = 'dummy@gmail.com'

    def setUp(self):
        self.client = Client()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.url = reverse(viewname=cls.url_name, kwargs=cls.url_kwargs)

        cls.user = User.objects.create_user(
            username=cls.dummy_username,
            password=cls.dummy_password,
            email=cls.dummy_email,
        )
