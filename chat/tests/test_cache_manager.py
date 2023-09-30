from django.test import TestCase

from account.models import User
from .mock_redis import replace_redis_with_mock
from ..cache_manager import get_or_set_from_db_chat_open_status
from ..redis_interface import RedisChatStatusInterface


class TestGetOrSetFromDbChatOpenStatus(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user',
                                            email='test@gmail.com',
                                            password='12345')

    def tearDown(self) -> None:
        self.user.is_running_chat = False
        self.user.save()

    @replace_redis_with_mock(asynchronous=True)
    async def test_get_negative_status_from_redis(self):
        self.user.is_running_chat = False
        await self.user.asave()
        RedisChatStatusInterface.update_chat_state(self.user)

        status = await get_or_set_from_db_chat_open_status(self.user.username)

        self.assertEqual(status, False)

    @replace_redis_with_mock(asynchronous=True)
    async def test_get_positive_status_from_redis(self):
        self.user.is_running_chat = True
        await self.user.asave()
        RedisChatStatusInterface.update_chat_state(self.user)

        status = await get_or_set_from_db_chat_open_status(self.user.username)

        self.assertEqual(status, True)

    @replace_redis_with_mock(asynchronous=True)
    async def test_get_negative_status_of_not_existing_user(self):
        status = await get_or_set_from_db_chat_open_status(owner_username='not_existing')

        self.assertEqual(status, False)

    @replace_redis_with_mock(asynchronous=True)
    async def test_get_status_chat_owner_user_from_db_and_set_to_redis(self):
        self.user.is_running_chat = True
        await self.user.asave()

        status = await get_or_set_from_db_chat_open_status(self.user.username)

        self.assertEqual(status, True)
        self.assertEqual(RedisChatStatusInterface.check_is_chat_open(self.user.username), True)
