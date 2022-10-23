from abc import ABCMeta, abstractmethod
from dataclasses import dataclass

import redis
from redis.commands.json.path import Path as RedisJsonPath
from tornado.log import app_log
from os import getenv

REDIS_HOST = getenv("REDIS_HOST")
if REDIS_HOST is None:
    raise TypeError("REDIS_HOST environment variable is set to None")

REDIS_PORT = getenv("REDIS_PORT")
if REDIS_PORT is None:
    raise TypeError("REDIS_PORT environment variable is set to None")


__session_cache = None


class CacheError(Exception):
    pass


@dataclass
class SessionEntry:
    """
    Session entry for user.
    """

    name_id: str = None
    saml_attrs: dict = None
    session_index: str = None


class Cache(metaclass=ABCMeta):
    """Interface for a cache

    key for this cache is the username. This is set during login and retrieved upon logout
    via the current_user property on the BaseHandler parent class
    """

    @abstractmethod
    def upsert(self, username: str, session_entry: SessionEntry):
        pass

    @abstractmethod
    def get(self, username: str) -> SessionEntry:
        pass

    @abstractmethod
    def remove(self, username: str):
        pass


class InMemoryCache(Cache):
    def __init__(self):
        self._cache = {}

    def upsert(self, username: str, session_entry: SessionEntry):
        if username in self._cache:
            app_log.warning(
                f"username = {session_entry.name_id} already stored in session cache. Updating session info"
            )
        else:
            app_log.info(f"inserting session info for {username}")
        self._cache[username] = session_entry

    def get(self, username: str) -> SessionEntry:
        if username not in self._cache:
            app_log.error(f"no session information for username = {username}")
            return SessionEntry()

        return self._cache[username]

    def remove(self, username: str):
        if username not in self._cache:
            app_log.error(f"no session information for username = {username}")
            return

        del self._cache[username]


class DisabledCache(Cache):
    def upsert(self, username: str, session_entry: SessionEntry):
        return

    def get(self, username: str) -> SessionEntry:
        return SessionEntry()

    def remove(self, username: str):
        return


class RedisCache(Cache):
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    def upsert(self, username: str, session_entry: SessionEntry):
        session_entry: dict = vars(session_entry)
        self.r.json().set(
            name=username,
            path=RedisJsonPath.root_path(),
            obj=session_entry,
            decode_keys=True,
        )

    def get(self, username: str) -> SessionEntry:
        session_entry: str = self.r.json().get(username, RedisJsonPath.root_path())
        session_entry: SessionEntry = SessionEntry(**session_entry)
        if not isinstance(session_entry, SessionEntry):
            raise TypeError(f"session entry for {username} is not of type SessionEntry")
        return session_entry

    def remove(self, username: str):
        self.r.json().delete(username, path=RedisJsonPath.root_path())


cache_map = {"redis": RedisCache, "in-memory": InMemoryCache, "disabled": DisabledCache}


def create(cache_type: str) -> Cache:
    """Factory for creating a cache

    Args:
        cache_type (str): type of cache. Allowed value = {redis, in-memory, disabled}

    Raises:
        CacheError: undefined cache type

    Returns:
        Cache: an instance of a cache
    """
    if cache_type not in cache_map:
        raise CacheError(
            f"couldn't create the cache. cache_type = {cache_type} is not allowed. Allowed values = {cache_map.keys()}"
        )

    return cache_map[cache_type]()


def register(cache: Cache):
    """Singleton function for registering a cache"""
    if not isinstance(cache, Cache):
        raise AttributeError(f"You must specify a Cache object, not = {type(cache)}")

    global __session_cache
    __session_cache = cache


def get():
    """Singleton method for getting a registered cache. You must register a cache before calling
    this function"""
    global __session_cache
    if not __session_cache:
        raise CacheError("you must register a cache first with register(cache)")

    return __session_cache
