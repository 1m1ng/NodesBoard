import redis.asyncio
from . import Config

r = None


class Redis:
    @staticmethod
    def init() -> redis.asyncio.Redis:
        global r
        r = redis.asyncio.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )
        return r

    @staticmethod
    def get() -> redis.asyncio.Redis:
        global r
        if r is None:
            r = Redis.init()
        return r
    