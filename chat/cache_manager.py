from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from account.models import User
from .redis_interface import RedisChatStatusInterface


async def get_or_set_from_db_chat_open_status(owner_username_slug):
    status = RedisChatStatusInterface.check_is_chat_open(owner_username_slug)

    if status is not None:
        return status

    else:
        try:
            chat_owner = await database_sync_to_async(User.objects.get)(username_slug=owner_username_slug)
        except ObjectDoesNotExist:
            return False

        RedisChatStatusInterface.update_chat_state(chat_owner)
        return chat_owner.is_running_chat
