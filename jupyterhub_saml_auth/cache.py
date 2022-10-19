from dataclasses import dataclass
from tornado.log import app_log


@dataclass
class SessionEntry:
    name_id: str
    saml_attrs: dict
    session_index: str


class InMemoryCache:
    def __init__(self):
        self._cache = {}

    def upsert(self, username: str, session_entry: SessionEntry):
        if username in self._cache:
            app_log.warning(
                f'username = {session_entry.name_id} already stored in session cache. Updating session info')
        else:
            app_log.info(f'inserting session info for {username}')
        self._cache[username] = session_entry

    def get(self, username: str) -> SessionEntry:
        if username not in self._cache:
            app_log.error(f'no session information for username = {username}')
            return SessionEntry(name_id=None, saml_attr=None, session_index=None)

        return self._cache[username]

    def remove(self, username: str):
        if username not in self._cache:
            app_log.error(f'no session information for username = {username}')
            return

        del self._cache[username]


class DisabledCache:
    def upsert(self, username: str, session_entry: SessionEntry):
        pass

    def get(self, username: str) -> SessionEntry:
        return SessionEntry(name_id=None, saml_attr=None, session_index=None)

    def remove(self, username: str):
        pass


class RedisCache:
    def upsert(self, username: str, session_entry: SessionEntry):
        pass

    def get(self, username: str) -> SessionEntry:
        return SessionEntry(name_id=None, saml_attr=None, session_index=None)

    def remove(self, username: str):
        pass
