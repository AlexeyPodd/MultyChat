import re
from unittest.mock import patch, Mock


class MockRedis:
    """Class with methods to replace methods of redis_instance"""
    def __init__(self):
        self.cache = dict()

    def get(self, key):
        res = self.cache.get(key)
        if res:
            res = str(res)
        return res

    def set(self, key, value):
        self.cache[key] = value
        return True

    def expire(self, key, time):
        return True

    def rpush(self, key, *values):
        lst = self.cache.get(key)
        if not lst:
            self.cache[key] = list(values)
        else:
            self.cache[key].extend(list(values))
        return len(values)

    def llen(self, key):
        lst = self.cache.get(key)
        if isinstance(lst, list):
            return len(self.cache[key])
        else:
            raise TypeError

    def ltrim(self, key, start, end):
        if end == -1:
            end = self.llen(key)
        else:
            end += 1

        lst = self.cache.get(key)
        if isinstance(lst, list):
            self.cache[key] = self.cache[key][start:end]
            return True
        else:
            raise TypeError

    def lrange(self, key, start, end):
        if end == -1:
            end = self.llen(key)
        else:
            end += 1

        lst = self.cache.get(key)
        if isinstance(lst, list):
            return self.cache[key][start:end]
        else:
            raise TypeError

    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
            return 1
        return 0

    def keys(self, regex):
        r = re.compile(regex.replace('*', '.+?'))
        all_keys = self.cache.keys()
        return list(filter(lambda k: re.fullmatch(r, k), all_keys))


def replace_redis_with_mock(test_func):
    """
    Decorator for mocking redis_instance.
    If needed more redis methods - you should write them in MockRedis class above, and add below as Mock side effect.
    """
    @patch('chat.redis_interface.redis_instance')
    def wrapper(test_obj, mock_redis):
        mock_redis_object = MockRedis()

        mock_redis.get = Mock(side_effect=mock_redis_object.get)
        mock_redis.set = Mock(side_effect=mock_redis_object.set)
        mock_redis.expire = Mock(side_effect=mock_redis_object.expire)
        mock_redis.rpush = Mock(side_effect=mock_redis_object.rpush)
        mock_redis.llen = Mock(side_effect=mock_redis_object.llen)
        mock_redis.ltrim = Mock(side_effect=mock_redis_object.ltrim)
        mock_redis.lrange = Mock(side_effect=mock_redis_object.lrange)
        mock_redis.delete = Mock(side_effect=mock_redis_object.delete)
        mock_redis.keys = Mock(side_effect=mock_redis_object.keys)

        return test_func(test_obj, mock_redis_object)
    return wrapper
