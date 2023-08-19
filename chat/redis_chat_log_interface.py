import redis
from typing import TypedDict, List

from multychats.settings import REDIS_HOST, REDIS_PORT, LENGTH_OF_CHAT_LOG, CHAT_LOGGING_DATA_TYPES


"""
Logging messages and its data will save in redis using keys, specified in CHAT_LOGGING_DATA_TYPES.
Full keys will have pattern chat__{chat_owner_slug}__{data_type}.
Always will be logged maximum number of last messages, specified in LENGTH_OF_CHAT_LOG.
"""


redis_instance = redis.Redis(host=REDIS_HOST,
                             port=REDIS_PORT,
                             db=0,
                             decode_responses=True)


MessageData = TypedDict('MessageData', {data_type[:-1]: str for data_type in CHAT_LOGGING_DATA_TYPES})


def log_chat_message(chat_owner_slug: str, **kwargs: MessageData) -> None:
    """
    Take arguments with names from CHAT_LOGGING_DATA_TYPES, but without last "s".
    """

    if len(kwargs) != len(CHAT_LOGGING_DATA_TYPES):
        raise TypeError("Wrong number of logging chat data. Check CHAT_LOGGING_DATA_TYPES in settings.py")

    data_types = {data_type: kwargs[data_type] for data_type in CHAT_LOGGING_DATA_TYPES}
    for log_type, log_data in data_types.items():
        redis_instance.rpush(f"chat__{chat_owner_slug}__{log_type}", log_data)
        redis_instance.ltrim(f"chat__{chat_owner_slug}__{log_type}", 1, LENGTH_OF_CHAT_LOG)


def get_chat_log_data(chat_owner_slug: str) -> List[MessageData]:
    """
    Returns list, where every message data dict have keys from CHAT_LOGGING_DATA_TYPES, but without last "s".
    """

    log_data = [redis_instance.lrange(f"chat__{chat_owner_slug}__{data_type}", 0, -1)
                for data_type in CHAT_LOGGING_DATA_TYPES]
    return [{data_type[:-1]: data[i] for i, data_type in enumerate(CHAT_LOGGING_DATA_TYPES)} for data in zip(*log_data)]
