import pytest
from unittest.mock import MagicMock
from jupyterhub_saml_auth.cache import *
from redis.commands.json.path import Path as RedisJsonPath

test_username = "user1"
test_session_entry = SessionEntry(
    name_id="mynameid",
    saml_attrs={"attr1": "attr1_val", "attr2": "attr2_val"},
    session_index="sessionindex",
)


class TestInMemoryCache:
    @pytest.fixture
    def in_memory_cache(self):
        in_memory_cache = InMemoryCache()
        in_memory_cache.upsert(test_username, test_session_entry)
        return in_memory_cache

    def test_upsert(self, in_memory_cache):
        assert test_session_entry == in_memory_cache._cache[test_username]

    def test_get(self, in_memory_cache):
        got = in_memory_cache.get(test_username)
        assert got == test_session_entry

        got = in_memory_cache.get("doesntexist")
        assert got == SessionEntry()

    def test_remove(self, in_memory_cache):
        in_memory_cache.remove(test_username)
        assert not in_memory_cache._cache

        in_memory_cache.remove("none")


class TestDisabledCache:
    @pytest.fixture
    def disabled_cache(self):
        return DisabledCache()

    def test_get(self, disabled_cache):
        should_be = SessionEntry()
        assert disabled_cache.get("something") == should_be

    def test_upsert(self, disabled_cache):
        disabled_cache.upsert(test_username, test_session_entry)

        should_be = SessionEntry()
        assert disabled_cache.get(test_username) == should_be

    def test_remove(self, disabled_cache):
        disabled_cache.remove(test_username)


class TestRedisCache:
    @pytest.fixture
    def setup_redis_cache(self):
        client = MagicMock
        json = MagicMock
        set = MagicMock()
        get = MagicMock(return_value=vars(test_session_entry))
        delete = MagicMock()

        json.set = set
        json.get = get
        json.delete = delete
        client.json = json

        redis_cache = RedisCache(client, {})
        return (redis_cache, client, json, set, get, delete)

    def test_upsert(self, setup_redis_cache):
        redis_cache, _, _, set, _, _ = setup_redis_cache
        redis_cache.upsert(test_username, test_session_entry)
        set.assert_called_with(
            name=test_username,
            path=RedisJsonPath.root_path(),
            obj=vars(test_session_entry),
            decode_keys=True,
        )

    def test_get(self, setup_redis_cache):
        redis_cache, _, _, _, get, _ = setup_redis_cache
        redis_cache.upsert(test_username, test_session_entry)
        got = redis_cache.get(test_username)
        assert got == test_session_entry

    def test_remove(self, setup_redis_cache):
        redis_cache, _, _, _, _, delete = setup_redis_cache
        redis_cache.remove(test_username)
        delete.assert_called_with(test_username, path=RedisJsonPath.root_path())


@pytest.fixture
def cache_details():
    cache_details = []
    for cache_type, cache_cls in cache_map.items():
        cache_spec = {"type": cache_type}
        if cache_cls.client_required:
            cache_spec.update({"client": MagicMock(), "client_kwargs": {}})
        cache_details.append((cache_type, cache_cls, cache_spec))

    return cache_details


def test_create(cache_details):

    for cache_type, cache_cls, cache_spec in cache_details:
        created_cache = create(cache_spec)
        assert isinstance(created_cache, cache_cls), cache_type

    with pytest.raises(CacheError):
        create({"type": "unspecified"})


def test_get_fail():
    """This test must come first before register() since register actually
    sets the cache
    """
    with pytest.raises(CacheError):
        get()


def test_register(cache_details):
    for cache_type, _, cache_spec in cache_details:
        try:
            created_cache = create(cache_spec)
            register(created_cache)
        except:
            pytest.fail(f"cache couldnt register = {cache_type}")

    class FakeCache:
        pass

    with pytest.raises(AttributeError):
        register(FakeCache())


def test_get_success():
    """This test must come after register() since register actually
    sets the cache
    """
    cache = get()
    assert isinstance(cache, Cache)
