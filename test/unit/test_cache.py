import pytest
from jupyterhub_saml_auth.cache import *

test_username = 'user1'
test_session_entry = SessionEntry(name_id='mynameid', saml_attrs={
    'attr1': 'attr1_val',
    'attr2': 'attr2_val'
}, session_index='sessionindex')


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

        got = in_memory_cache.get('doesntexist')
        assert got == SessionEntry()

    def test_remove(self, in_memory_cache):
        in_memory_cache.remove(test_username)
        assert not in_memory_cache._cache

        in_memory_cache.remove('none')


class TestDisabledCache:
    @pytest.fixture
    def disabled_cache(self):
        return DisabledCache()

    def test_get(self, disabled_cache):
        should_be = SessionEntry()
        assert disabled_cache.get('something') == should_be

    def test_upsert(self, disabled_cache):
        disabled_cache.upsert(test_username, test_session_entry)

        should_be = SessionEntry()
        assert disabled_cache.get(test_username) == should_be

    def test_remove(self, disabled_cache):
        disabled_cache.remove(test_username)


def test_create():
    assert isinstance(create('in-memory'), InMemoryCache)
    assert isinstance(create('disabled'), DisabledCache)

    with pytest.raises(CacheError):
        create('unspecified')


def test_get_fail():
    """This test must come first before register() since register actually
    sets the cache
    """
    with pytest.raises(CacheError):
        get()


def test_register():
    for cache_name, cache in cache_map.items():
        try:
            register(cache())
        except:
            pytest.fail(f"cache couldnt register = {cache_name}")

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
