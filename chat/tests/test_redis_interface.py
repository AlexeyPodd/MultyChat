from django.test import TestCase, SimpleTestCase

from account.models import User
from multychats.settings import LENGTH_OF_CHAT_LOG, CHAT_LOGGING_DATA_TYPES_PLURAL
from .mock_redis import replace_redis_with_mock
from ..redis_interface import RedisChatStatusInterface, RedisChatLogInterface


class TestRedisChatStatusInterface(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_mock', password='dsogpdopfg', email='testttt@gamil.com')

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test_update_chat_state_open(self, mock_redis_instance):
        self.user.is_running_chat = True

        RedisChatStatusInterface.update_chat_state(self.user)

        self.assertEqual(mock_redis_instance.cache[f"chat__{self.user.username}__is_running_chat"], 1)

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test_update_chat_state_close(self, mock_redis_instance):
        self.user.is_running_chat = False

        RedisChatStatusInterface.update_chat_state(self.user)

        self.assertEqual(mock_redis_instance.cache[f"chat__{self.user.username}__is_running_chat"], 0)


class TestRedisChatLogInterface(SimpleTestCase):
    chat_owner_username = 'owner_username'
    author_username = 'author_username'
    author_status = 'some_status'
    message = 'message'

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test__pop_all_data(self, mock_redis_instance):
        cached_data = {
            "author_usernames": [
                self.author_username,
                self.author_username,
                self.author_username,
                'user_2',
                'user_2',
            ],
            "author_statuses": [
                self.author_status,
                self.author_status,
                self.author_status,
                'user',
                'moder',
            ],
            "messages": [
                self.message,
                self.message,
                self.message,
                'i want to be moder',
                'i am moder now!',
            ],
        }
        for log_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
            mock_redis_instance.cache[f"chat__{self.chat_owner_username}__{log_type}"] = cached_data[log_type]

        data = RedisChatLogInterface._pop_all_data(chat_owner_username=self.chat_owner_username)

        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 3)
        for i, data_list in enumerate(data):
            self.assertEqual(data_list, cached_data[CHAT_LOGGING_DATA_TYPES_PLURAL[i]])

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test__pop_all_data_from_empty_cache(self, mock_redis_instance):
        empty_data = RedisChatLogInterface._pop_all_data(chat_owner_username='test')

        self.assertTrue(isinstance(empty_data, list))
        self.assertEqual(len(empty_data), 3)
        for data_list in empty_data:
            self.assertTrue(isinstance(data_list, list))
            self.assertEqual(len(data_list), 0)

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test__write_log_data(self, mock_redis_instance):
        cached_data = {
            "author_usernames": [
                self.author_username,
                self.author_username,
                self.author_username,
                'user_2',
                'user_2',
            ],
            "author_statuses": [
                self.author_status,
                self.author_status,
                self.author_status,
                'user',
                'moder',
            ],
            "messages": [
                self.message,
                self.message,
                self.message,
                'i want to be moder',
                'i am moder now!',
            ],
        }

        RedisChatLogInterface._write_log_data(chat_owner_username=self.chat_owner_username,
                                              log_data_list=iter([cached_data[data_type]
                                                                  for data_type in CHAT_LOGGING_DATA_TYPES_PLURAL]))

        for data_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
            self.assertEqual(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__{data_type}"],
                             cached_data[data_type])

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test__get_logged_chat_owner_usernames(self, mock_redis_instance):
        usernames = ['test', 'user_test', 'another_user']
        for username in usernames:
            mock_redis_instance.cache[f'chat__{username}__messages'] = ['hello', 'world']

        cached_chat_owners = RedisChatLogInterface._get_logged_chat_owner_usernames()

        self.assertEqual(set(usernames), set(cached_chat_owners))

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test_log_chat_message_one_message(self, mock_redis_instance):
        RedisChatLogInterface.log_chat_message(chat_owner_username=self.chat_owner_username,
                                               author_username=self.author_username,
                                               author_status=self.author_status,
                                               message=self.message)

        self.assertEqual(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__author_usernames"][0],
                         self.author_username)
        self.assertEqual(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__author_statuses"][0],
                         self.author_status)
        self.assertEqual(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__messages"][0],
                         self.message)

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test_log_chat_message_more_then_cache_capacity(self, mock_redis_instance):
        for i in range(LENGTH_OF_CHAT_LOG + 5):
            RedisChatLogInterface.log_chat_message(chat_owner_username=self.chat_owner_username,
                                                   author_username=self.author_username,
                                                   author_status=self.author_status,
                                                   message=self.message + str(i))

        for log_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
            self.assertEqual(len(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__{log_type}"]),
                             LENGTH_OF_CHAT_LOG)

        self.assertEqual(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__messages"][-1],
                         self.message + str(LENGTH_OF_CHAT_LOG + 4))
        self.assertEqual(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__messages"][0],
                         self.message + str(5))

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test_get_chat_log_data(self, mock_redis_instance):
        cached_data = {
            "author_usernames": [
                self.author_username,
                self.author_username,
                self.author_username,
                'user_2',
                'user_2',
            ],
            "author_statuses": [
                self.author_status,
                self.author_status,
                self.author_status,
                'user',
                'moder',
            ],
            "messages": [
                self.message,
                self.message,
                self.message,
                'i want to be moder',
                'i am moder now!',
            ],
        }
        for log_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
            mock_redis_instance.cache[f"chat__{self.chat_owner_username}__{log_type}"] = cached_data[log_type]

        data = RedisChatLogInterface.get_chat_log_data(self.chat_owner_username)

        self.assertTrue(isinstance(data, list))
        for i, msg_data in enumerate(data):
            self.assertEqual(cached_data["author_usernames"][i], msg_data['author_username'])
            self.assertEqual(cached_data["author_statuses"][i], msg_data['author_status'])
            self.assertEqual(cached_data["messages"][i], msg_data['message'])

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test_delete_user_messages_in_every_chat(self, mock_redis_instance):
        chat_owners = [self.chat_owner_username, self.author_username, 'user_3']
        cached_data_1 = {
            "author_usernames": [
                self.author_username,
                self.author_username,
                self.author_username,
                'user_2',
                'user_2',
            ],
            "author_statuses": [
                self.author_status,
                self.author_status,
                self.author_status,
                'user',
                'moder',
            ],
            "messages": [
                self.message,
                self.message,
                self.message,
                'i want to be moder',
                'i am moder now!',
            ],
        }
        cached_data_2 = {
            "author_usernames": [
                self.author_username,
                'user_2',
            ],
            "author_statuses": [
                self.author_status,
                'user',
            ],
            "messages": [
                self.message,
                'hello',
            ],
        }
        cached_data_3 = {
            "author_usernames": [
                'user_2',
            ],
            "author_statuses": [
                'married',
            ],
            "messages": [
                'i\'m wierd',
            ],
        }
        for chat_owner_username, cached_data in zip(chat_owners, (cached_data_1, cached_data_2, cached_data_3)):
            for log_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
                mock_redis_instance.cache[f"chat__{chat_owner_username}__{log_type}"] = cached_data[log_type]

        RedisChatLogInterface.delete_user_messages(self.author_username, None)

        for chat_owner_username in chat_owners:

            # checking if length of messages, length of authors and length of statuses are equal
            data_types_cache_lengthes = set()
            for log_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
                data_types_cache_lengthes.add(
                    len(mock_redis_instance.cache[f"chat__{chat_owner_username}__{log_type}"]))
            self.assertEqual(len(data_types_cache_lengthes), 1)

            # checking if there is author with deleted username
            self.assertNotIn(self.author_username,
                             mock_redis_instance.cache[f"chat__{chat_owner_username}__author_usernames"])

        # Checking all cache lengthes are equal with initial data, but without deleted user messages data
        for chat_owner_username, cached_data in zip(chat_owners, (cached_data_1, cached_data_2, cached_data_3)):
            self.assertEqual(len(mock_redis_instance.cache[f"chat__{chat_owner_username}__author_usernames"]),
                             len(tuple(filter(lambda u: u != self.author_username, cached_data["author_usernames"]))))

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test_delete_user_messages_in_specific_chat(self, mock_redis_instance):
        chat_owners = [self.chat_owner_username, self.author_username, 'user_3']
        cached_data_1 = {
            "author_usernames": [
                self.author_username,
                self.author_username,
                self.author_username,
                'user_2',
                'user_2',
            ],
            "author_statuses": [
                self.author_status,
                self.author_status,
                self.author_status,
                'user',
                'moder',
            ],
            "messages": [
                self.message,
                self.message,
                self.message,
                'i want to be moder',
                'i am moder now!',
            ],
        }
        cached_data_2 = {
            "author_usernames": [
                self.author_username,
                'user_2',
            ],
            "author_statuses": [
                self.author_status,
                'user',
            ],
            "messages": [
                self.message,
                'hello',
            ],
        }
        cached_data_3 = {
            "author_usernames": [
                'user_2',
            ],
            "author_statuses": [
                'married',
            ],
            "messages": [
                'i\'m wierd',
            ],
        }

        for chat_owner_username, cached_data in zip(chat_owners, (cached_data_1, cached_data_2, cached_data_3)):
            for log_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
                mock_redis_instance.cache[f"chat__{chat_owner_username}__{log_type}"] = cached_data[log_type]

        RedisChatLogInterface.delete_user_messages(self.author_username, chat_owners[0])

        # checking if length of messages, length of authors and length of statuses are equal
        for chat_owner_username in chat_owners:
            data_types_cache_lengthes = set()
            for log_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
                data_types_cache_lengthes.add(
                    len(mock_redis_instance.cache[f"chat__{chat_owner_username}__{log_type}"]))
            self.assertEqual(len(data_types_cache_lengthes), 1)

        # For chat, where user messages were deleted -------------------------------------------------------------------
        # checking if there is author with deleted username
        self.assertNotIn(self.author_username,
                         mock_redis_instance.cache[f"chat__{chat_owners[0]}__author_usernames"])

        # Checking all cache lengthes are equal with initial data, but without deleted user messages data
        self.assertEqual(len(mock_redis_instance.cache[f"chat__{chat_owners[0]}__author_usernames"]),
                         len(tuple(filter(lambda u: u != self.author_username, cached_data_1["author_usernames"]))))

        # For chats, where user messages were NOT deleted --------------------------------------------------------------
        # in second chat there was deleted author, should be still there
        self.assertIn(self.author_username, mock_redis_instance.cache[f"chat__{chat_owners[1]}__author_usernames"])
        # in third chat there was NOT deleted author, should be still NOT there
        self.assertNotIn(self.author_username, mock_redis_instance.cache[f"chat__{chat_owners[2]}__author_usernames"])

        # Checking second cache length are equal with initial data
        for chat_owner_username, cached_data in zip(chat_owners[1:], (cached_data_2, cached_data_3)):
            self.assertEqual(len(mock_redis_instance.cache[f"chat__{chat_owner_username}__author_usernames"]),
                             len(cached_data["author_usernames"]))

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test_change_user_status(self, mock_redis_instance):
        cached_data = {
            "author_usernames": [
                self.chat_owner_username,
                self.author_username,
                self.author_username,
                'user_2',
                'user_2',
            ],
            "author_statuses": [
                'owner',
                self.author_status,
                self.author_status,
                'user',
                'moder',
            ],
            "messages": [
                self.message,
                self.message,
                self.message,
                'i want to be moder',
                'i am moder now!',
            ],
        }
        for log_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
            mock_redis_instance.cache[f"chat__{self.chat_owner_username}__{log_type}"] = cached_data[log_type]

        new_status = 'new_status'
        RedisChatLogInterface.change_user_status(self.chat_owner_username, self.author_username, new_status=new_status)

        self.assertEqual(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__author_usernames"],
                         cached_data["author_usernames"])
        self.assertEqual(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__messages"],
                         cached_data["messages"])
        expected_statuses = [new_status if cached_data["author_usernames"][i] == self.author_username else old_status
                             for i, old_status in enumerate(cached_data["author_statuses"])]
        self.assertEqual(mock_redis_instance.cache[f"chat__{self.chat_owner_username}__author_statuses"],
                         expected_statuses)

    @replace_redis_with_mock(pass_mock_to_func=True)
    def test_change_user_status_with_empty_log(self, mock_redis_instance):
        new_status = 'new_status'
        RedisChatLogInterface.change_user_status(self.chat_owner_username, self.author_username, new_status=new_status)

        self.assertFalse(mock_redis_instance.cache)
