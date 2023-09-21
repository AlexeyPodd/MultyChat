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


class TestHomeView(TestView):
    url_name = 'chat:home'

    def test_GET(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/home.html')


class TestChatRoomView(TestView):
    url_name = 'chat:chat-room'
    url_kwargs = {'chat_owner_slug': 'dummy_test_user'}

    def test_GET(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/room.html')

    def test_GET_not_existing_user(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        url = reverse(viewname=self.url_name, kwargs={'chat_owner_slug': 'non_existing'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_GET_not_logged_in(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('account:login') + '?next=' + self.url)


class TestBlackListView(TestView):
    url_name = 'chat:black-list'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.second_user = User.objects.create_user(
            username=cls.dummy_username+'2',
            password=cls.dummy_password+'123',
            email='j'+cls.dummy_email,
        )

    def test_GET(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/manage_user_list.html')

    def test_GET_not_logged_in(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('account:login') + '?next=' + self.url)

    def test_POST_removes_user_from_black_list(self):
        self.user.black_listed_users.add(self.second_user)
        self.client.login(username=self.dummy_username, password=self.dummy_password)

        response = self.client.post(self.url, data={'username': self.second_user.username})

        self.user.refresh_from_db()
        self.assertFalse(self.user.black_listed_users.filter(pk=self.second_user.pk).exists())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/manage_user_list.html')

    def test_POST_no_data(self):
        self.user.black_listed_users.add(self.second_user)
        self.client.login(username=self.dummy_username, password=self.dummy_password)

        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, 404)
        self.assertTrue(self.user.black_listed_users.filter(pk=self.second_user.pk).exists())

    def test_POST_tries_to_remove_not_existing_user(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)

        response = self.client.post(self.url, data={'username': 'not_existing'})

        self.assertEqual(response.status_code, 404)

    def test_POST_tries_to_remove_not_black_listed_user(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)

        response = self.client.post(self.url, data={'username': self.second_user.username})

        self.user.refresh_from_db()
        self.assertFalse(self.user.black_listed_users.filter(pk=self.second_user.pk).exists())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/manage_user_list.html')
