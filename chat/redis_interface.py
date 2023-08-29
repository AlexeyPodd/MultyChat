import redis
from typing import TypedDict, List

from account.models import User
from multychats.settings import REDIS_HOST, REDIS_PORT, LENGTH_OF_CHAT_LOG, CHAT_LOGGING_DATA_TYPES, \
    CHAT_AUTO_DELETE_DELAY, CHAT_LOGGING_DATA_TYPES_PLURAL

"""
Logging messages and its data will save in redis using keys, specified in CHAT_LOGGING_DATA_TYPES.
Full keys will have pattern chat__{chat_owner_username}__{data_type}.
Always will be logged maximum number of last messages, specified in LENGTH_OF_CHAT_LOG.
"""


redis_instance = redis.Redis(host=REDIS_HOST,
                             port=REDIS_PORT,
                             db=0,
                             decode_responses=True)


MessageData = TypedDict('MessageData', {data_type: str for data_type in CHAT_LOGGING_DATA_TYPES})


class RedisChatLogInterface:
    @staticmethod
    def log_chat_message(chat_owner_username: str, author_username: str, message: str) -> None:
        log_data = [author_username, message]

        for log_type, log_data in zip(CHAT_LOGGING_DATA_TYPES_PLURAL, log_data):
            redis_instance.rpush(f"chat__{chat_owner_username}__{log_type}", log_data)

            chat_length = redis_instance.llen(f"chat__{chat_owner_username}__{log_type}")
            trim_index = 0 if chat_length < LENGTH_OF_CHAT_LOG else chat_length - LENGTH_OF_CHAT_LOG
            redis_instance.ltrim(f"chat__{chat_owner_username}__{log_type}", trim_index, -1)

    @staticmethod
    def get_chat_log_data(chat_owner_username: str) -> List[MessageData]:
        log_data = [redis_instance.lrange(f"chat__{chat_owner_username}__{data_type}", 0, -1)
                    for data_type in CHAT_LOGGING_DATA_TYPES_PLURAL]
        return [{data_type: data[i] for i, data_type in enumerate(CHAT_LOGGING_DATA_TYPES)} for data in zip(*log_data)]

    @classmethod
    def delete_user_messages(cls, chat_owner_username: str, username: str) -> None:
        log_data = []
        for data_type in CHAT_LOGGING_DATA_TYPES_PLURAL:
            log_data.append(redis_instance.lrange(f"chat__{chat_owner_username}__{data_type}", 0, -1))
            redis_instance.delete(f"chat__{chat_owner_username}__{data_type}")

        log_data = zip(*filter(lambda data: data[0] != username, zip(*log_data)))
        for log_type, log_data in zip(CHAT_LOGGING_DATA_TYPES_PLURAL, log_data):
            redis_instance.rpush(f"chat__{chat_owner_username}__{log_type}", *log_data)


class RedisChatStatusInterface:
    @staticmethod
    def update_chat_state(owner: User) -> None:
        redis_instance.set(f"chat__{owner.username}__is_running_chat", int(owner.is_running_chat))
        redis_instance.expire(f"chat__{owner.username}__is_running_chat", CHAT_AUTO_DELETE_DELAY)

    @staticmethod
    def check_is_chat_open(owner_username: str) -> [bool, None]:
        try:
            return bool(int(redis_instance.get(f"chat__{owner_username}__is_running_chat")))
        except TypeError:
            return None
