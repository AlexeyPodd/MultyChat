import re
from datetime import timedelta
from typing import List

from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from account.models import User
from .base_test_view import TestView
from .mock_redis import replace_redis_with_mock
from ..models import Ban


class TestHomeView(TestView):
    url_name = 'chat:home'

    def test_GET(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/home.html')


class TestChatRoomView(TestView):
    url_name = 'chat:chat-room'
    url_kwargs = {'chat_owner_slug': 'dummy_test_user'}

    def test_GET_logged_in(self):
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
            username=cls.dummy_username + '2',
            password=cls.dummy_password + '123',
            email='j' + cls.dummy_email,
        )

    def test_GET_logged_in(self):
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


class TestModeratorListView(TestView):
    url_name = 'chat:moder-list'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.second_user = User.objects.create_user(
            username=cls.dummy_username + '2',
            password=cls.dummy_password + '123',
            email='j' + cls.dummy_email,
        )

    def test_GET_logged_in(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/manage_user_list.html')

    def test_GET_not_logged_in(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('account:login') + '?next=' + self.url)

    @replace_redis_with_mock
    def test_POST_removes_user_from_moder_list(self):
        self.user.moderators.add(self.second_user)
        self.client.login(username=self.dummy_username, password=self.dummy_password)

        response = self.client.post(self.url, data={'username': self.second_user.username})

        self.user.refresh_from_db()
        self.assertFalse(self.user.moderators.filter(pk=self.second_user.pk).exists())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/manage_user_list.html')

    @replace_redis_with_mock
    def test_POST_no_data(self):
        self.user.moderators.add(self.second_user)
        self.client.login(username=self.dummy_username, password=self.dummy_password)

        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, 404)
        self.assertTrue(self.user.moderators.filter(pk=self.second_user.pk).exists())

    @replace_redis_with_mock
    def test_POST_tries_to_remove_not_existing_user(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)

        response = self.client.post(self.url, data={'username': 'not_existing'})

        self.assertEqual(response.status_code, 404)

    @replace_redis_with_mock
    def test_POST_tries_to_remove_not_moderator_user(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)

        response = self.client.post(self.url, data={'username': self.second_user.username})

        self.user.refresh_from_db()
        self.assertFalse(self.user.moderators.filter(pk=self.second_user.pk).exists())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/manage_user_list.html')


class TestBannedListView(TestView):
    url_name = 'chat:banned-list'

    def test_GET_logged_in(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/banned_users_list.html')

    def test_GET_not_logged_in(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('account:login') + '?next=' + self.url)

    def test_GET_queryset(self):
        # Creating users to ban
        user1 = User.objects.create_user(username='testuser1', email='1@gmail.com', password='123456789')
        user2 = User.objects.create_user(username='testuser2', email='2@gmail.com', password='123456789')
        user3 = User.objects.create_user(username='testuser3', email='3@gmail.com', password='123456789')
        user4 = User.objects.create_user(username='testuser4', email='4@gmail.com', password='123456789')

        b1 = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=user1,
                                time_end=timezone.now() + timedelta(minutes=20))
        b2 = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=user1,
                                time_end=timezone.now() + timedelta(minutes=25))
        b3 = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=user1,
                                time_end=timezone.now() + timedelta(days=1))
        b4 = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=user2,
                                time_end=timezone.now() + timedelta(minutes=30))
        b5 = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=user2,
                                time_end=timezone.now() + timedelta(hours=20))
        b6 = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=user3,
                                time_end=timezone.now() + timedelta(minutes=550))
        b7 = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=user3,
                                time_end=timezone.now() + timedelta(minutes=20))
        b8 = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=user4,
                                time_end=timezone.now())
        b9 = Ban.objects.create(chat_owner=user1, banned_by=self.user, banned_user=user4,
                                time_end=timezone.now() + timedelta(minutes=20))

        right_pks = [ban.pk for ban in (b3, b5, b6)]

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url)

        self.assertQuerysetEqual(response.context.get('bans'),
                                 Ban.objects.filter(pk__in=right_pks).order_by('banned_user'))


class TestUnbanAjaxView(TestView):
    url_name = 'chat:ajax-unban-user'

    another_username = 'another_user'
    another_email = 'another_email'
    another_password = 'another_password'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.banned_user = User.objects.create_user(username='banned_test_user',
                                                   email='banned@gmail.com', password='123')
        cls.another_user = User.objects.create_user(username=cls.another_username, email=cls.another_email,
                                                    password=cls.another_password)

    def test_GET_not_allowed(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_POST_not_logged_in(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 403)

    def test_POST_tries_to_delete_specified_ban_not_admin(self):
        ban = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                                 time_end=timezone.now() + timedelta(minutes=20))

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.post(self.url, data={'banId': ban.pk})

        self.assertEqual(response.status_code, 403)

    def test_POST_tries_to_delete_specified_ban_not_digit_id(self):
        self.user.is_staff = True
        self.user.save()
        ban = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                                 time_end=timezone.now() + timedelta(minutes=20))

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.post(self.url, data={'banId': ban.chat_owner.username})

        self.assertEqual(response.status_code, 400)

        self.user.is_staff = False
        self.user.save()

    def test_POST_tries_to_delete_specified_not_existing_ban(self):
        self.user.is_staff = True
        self.user.save()
        ban = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                                 time_end=timezone.now() + timedelta(minutes=20))

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.post(self.url, data={'banId': ban.id+1})

        self.assertEqual(response.status_code, 404)

        self.user.is_staff = False
        self.user.save()

    def test_POST_deletes_specified_ban(self):
        self.user.is_staff = True
        self.user.save()
        ban = Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                                 time_end=timezone.now() + timedelta(minutes=20))

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.post(self.url, data={'banId': ban.id})

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'user_unbanned': self.banned_user.username})

        self.user.is_staff = False
        self.user.save()

    def test_POST_tries_to_delete_all_bans_of_specified_user_in_specified_not_existing_chat(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.post(self.url, data={'bannedUsername': self.banned_user.username,
                                                    'chatOwnerUsername': 'not_existing_user'})

        self.assertEqual(response.status_code, 404)

    def test_POST_tries_to_delete_all_bans_of_specified_user_in_all_chats_not_admin(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.post(self.url, data={'bannedUsername': self.banned_user.username})

        self.assertEqual(response.status_code, 403)

    def test_POST_tries_to_delete_all_bans_of_specified_not_existing_user_in_specified_chat(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.post(self.url, data={'bannedUsername': 'not_existing_user',
                                                    'chatOwnerUsername': self.user.username})

        self.assertEqual(response.status_code, 404)

    def test_POST_tries_to_delete_all_bans_of_specified_user_in_specified_chat_but_have_no_permission(self):
        self.client.login(username=self.another_username, password=self.another_password)
        response = self.client.post(self.url, data={'bannedUsername': self.banned_user.username,
                                                    'chatOwnerUsername': self.user.username})

        self.assertEqual(response.status_code, 403)

    def test_POST_tries_to_delete_all_indefinite_bans_of_specified_user_in_specified_chat_by_moderator(self):
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user)
        self.user.moderators.add(self.another_user)

        self.client.login(username=self.another_username, password=self.another_password)
        response = self.client.post(self.url, data={'bannedUsername': self.banned_user.username,
                                                    'chatOwnerUsername': self.user.username})

        self.assertEqual(response.status_code, 403)

        self.user.moderators.remove(self.another_user)

    def test_POST_tries_to_delete_all_bans_of_specified_user_in_specified_chat_by_moderator_but_there_is_no_bans(self):
        self.user.moderators.add(self.another_user)

        self.client.login(username=self.another_username, password=self.another_password)
        response = self.client.post(self.url, data={'bannedUsername': self.banned_user.username,
                                                    'chatOwnerUsername': self.user.username})

        self.assertEqual(response.status_code, 404)

        self.user.moderators.remove(self.another_user)

    def test_POST_deletes_all_bans_of_specified_user_in_specified_chat_by_moderator(self):
        self.user.moderators.add(self.another_user)
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                           time_end=timezone.now() + timedelta(minutes=20))
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                           time_end=timezone.now() + timedelta(minutes=20))
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                           time_end=timezone.now() + timedelta(days=2))

        self.client.login(username=self.another_username, password=self.another_password)
        response = self.client.post(self.url, data={'bannedUsername': self.banned_user.username,
                                                    'chatOwnerUsername': self.user.username})

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'user_unbanned': self.banned_user.username})
        self.assertFalse(self.banned_user.bans.exists())

        self.user.moderators.remove(self.another_user)

    def test_POST_deletes_all_bans_of_specified_user_in_specified_chat_by_owner(self):
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user)
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                           time_end=timezone.now() + timedelta(minutes=20))
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                           time_end=timezone.now() + timedelta(days=2))

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.post(self.url, data={'bannedUsername': self.banned_user.username,
                                                    'chatOwnerUsername': self.user.username})

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'user_unbanned': self.banned_user.username})
        self.assertFalse(self.banned_user.bans.exists())

    def test_POST_deletes_all_bans_of_specified_user_in_specified_chat_by_admin(self):
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user)
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                           time_end=timezone.now() + timedelta(minutes=20))
        Ban.objects.create(chat_owner=self.user, banned_by=self.user, banned_user=self.banned_user,
                           time_end=timezone.now() + timedelta(days=2))
        self.another_user.is_staff = True
        self.another_user.save()

        self.client.login(username=self.another_username, password=self.another_password)
        response = self.client.post(self.url, data={'bannedUsername': self.banned_user.username,
                                                    'chatOwnerUsername': self.user.username})

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'user_unbanned': self.banned_user.username})
        self.assertFalse(self.banned_user.bans.exists())

        self.another_user.is_staff = False
        self.another_user.save()


class TestGetChatBannedInfoAjaxView(TestView):
    url_name = 'chat:ajax-banned-list'

    another_username = 'another_user'
    another_email = 'another_email'
    another_password = 'another_password'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.banned_user = User.objects.create_user(username='banned_test_user',
                                                   email='banned@gmail.com', password='123')
        cls.another_user = User.objects.create_user(username=cls.another_username, email=cls.another_email,
                                                    password=cls.another_password)
        cls.url += f'?owner={cls.dummy_username}'

        cls.b1 = Ban.objects.create(chat_owner=cls.user, banned_by=cls.user, banned_user=cls.banned_user)
        Ban.objects.create(chat_owner=cls.user, banned_by=cls.user, banned_user=cls.banned_user,
                           time_end=timezone.now() + timedelta(minutes=20))
        cls.b2 = Ban.objects.create(chat_owner=cls.user, banned_by=cls.user, banned_user=cls.another_user,
                                    time_end=timezone.now() + timedelta(days=2))

        expected_queryset = Ban.objects.filter(pk__in=[cls.b1.pk, cls.b2.pk]).order_by('banned_user')
        cls.expected_data = {"data": list(expected_queryset.values('banned_user__username', 'time_start',
                                                                   'time_end', 'banned_by__username'))}
        for data in cls.expected_data['data']:
            data['time_start'] = re.sub(r'[0-9]{3}\+00:00', 'Z', data['time_start'].isoformat())
            if data['time_end']:
                data['time_end'] = re.sub(r'[0-9]{3}\+00:00', 'Z', data['time_end'].isoformat())

    def test_POST_not_allowed(self):
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, 405)

    def test_GET_not_logged_in(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_GET_not_existing_chat_owner(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + '123dff')

        self.assertEqual(response.status_code, 404)

    def test_GET_have_no_permission(self):
        self.client.login(username=self.another_username, password=self.another_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_GET_by_owner(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), self.expected_data)

    def test_GET_by_admin(self):
        self.another_user.is_staff = True
        self.another_user.save()

        self.client.login(username=self.another_username, password=self.another_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), self.expected_data)

        self.another_user.is_staff = False
        self.another_user.save()

    def test_GET_by_moderator(self):
        self.user.moderators.add(self.another_user)

        self.client.login(username=self.another_username, password=self.another_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), self.expected_data)

        self.user.moderators.remove(self.another_user)


class TestGetBannedAdminInfoAjaxView(TestView):
    url_name = 'chat:ajax-search-admin-banned-list'

    another_username = 'another_user'
    another_email = 'another_email'
    another_password = 'another_password'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user.is_staff = True
        cls.user.save()
        cls.banned_user = User.objects.create_user(username='banned_test_user',
                                                   email='banned@gmail.com', password='123')
        cls.another_user = User.objects.create_user(username=cls.another_username, email=cls.another_email,
                                                    password=cls.another_password)

        cls.b1 = Ban.objects.create(chat_owner=cls.user, banned_by=cls.user, banned_user=cls.banned_user)
        cls.b2 = Ban.objects.create(chat_owner=cls.user, banned_by=cls.user, banned_user=cls.banned_user,
                                    time_end=timezone.now() + timedelta(minutes=20))
        cls.b3 = Ban.objects.create(chat_owner=cls.another_user, banned_by=cls.user, banned_user=cls.banned_user,
                                    time_end=timezone.now() + timedelta(hours=20))
        cls.b4 = Ban.objects.create(chat_owner=cls.user, banned_by=cls.user, banned_user=cls.another_user,
                                    time_end=timezone.now() + timedelta(days=2))

    @staticmethod
    def _get_expected_data(pks: List[int]):
        expected_queryset = (Ban.objects.filter(pk__in=pks)
                             .order_by('banned_user', 'chat_owner', F('time_end').desc(nulls_first=True)))
        expected_data = {"data": list(expected_queryset.values('id', 'banned_user__username', 'chat_owner__username',
                                                               'time_start', 'time_end', 'banned_by__username'))}
        for data in expected_data['data']:
            data['time_start'] = re.sub(r'[0-9]{3}\+00:00', 'Z', data['time_start'].isoformat())
            if data['time_end']:
                data['time_end'] = re.sub(r'[0-9]{3}\+00:00', 'Z', data['time_end'].isoformat())

        return expected_data

    def test_POST_not_allowed(self):
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, 405)

    def test_GET_not_logged_in(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_GET_not_admin(self):
        self.user.is_staff = False
        self.user.save()

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

        self.user.is_staff = True
        self.user.save()

    def test_GET_not_digit_all_bans_parameter(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + f'?owner={self.dummy_username}&user={self.banned_user.username}&all=t')

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'error': 'Non-Numeric Parameter \'all\''})

    def test_GET_no_owner_user_and_banned_user_parameters(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + '?all=0')

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'error': 'No Search Criteria'})

    def test_GET_not_existing_owner_user(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + f'?owner={self.dummy_username + "ttt"}')

        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(str(response.content, encoding='utf8'),
                             {'error': 'Not Founded', 'model': 'User (chat owner)'})

    def test_GET_not_existing_banned_user(self):
        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + f'?user={self.banned_user.username + "ttt"}')

        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(str(response.content, encoding='utf8'),
                             {'error': 'Not Founded', 'model': 'User (banned user)'})

    def test_GET_queryset_specified_owner_and_banned_all_bans(self):
        expected_data = self._get_expected_data([self.b1.pk, self.b2.pk])

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + f'?owner={self.dummy_username}&user={self.banned_user.username}&all=1')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_data)

    def test_GET_queryset_specified_owner_and_banned_not_all_bans(self):
        expected_data = self._get_expected_data([self.b1.pk])

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + f'?owner={self.dummy_username}&user={self.banned_user.username}&all=0')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_data)

    def test_GET_queryset_specified_owner_all_bans(self):
        expected_data = self._get_expected_data([self.b1.pk, self.b2.pk, self.b4.pk])

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + f'?owner={self.dummy_username}&all=1')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_data)

    def test_GET_queryset_specified_owner_not_all_bans(self):
        expected_data = self._get_expected_data([self.b1.pk, self.b4.pk])

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + f'?owner={self.dummy_username}&all=0')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_data)

    def test_GET_queryset_specified_user_all_bans(self):
        expected_data = self._get_expected_data([self.b1.pk, self.b2.pk, self.b3.pk])

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + f'?user={self.banned_user.username}&all=1')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_data)

    def test_GET_queryset_specified_user_not_all_bans(self):
        expected_data = self._get_expected_data([self.b1.pk, self.b3.pk])

        self.client.login(username=self.dummy_username, password=self.dummy_password)
        response = self.client.get(self.url + f'?user={self.banned_user.username}&all=0')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_data)
