from jupyterhub.auth import Authenticator
from jupyterhub.utils import url_path_join
from traitlets import Unicode, validate, Set, Callable, Dict, Bool
import os

from .handlers import (
    ACSHandler,
    MetadataHandler,
    SamlLoginHandler,
    SamlLogoutHandler,
)
from . import cache


class SAMLAuthenticator(Authenticator):

    acs_handler = ACSHandler
    metadata_handler = MetadataHandler
    login_handler = SamlLoginHandler
    logout_handler = SamlLogoutHandler

    session_cookie_names = Set(
        help="""
        Cookie names for managing SAML session that would be cleared upon
        logout
        """,
        config=True,
    )

    saml_settings_path = Unicode(
        default_value="/etc/saml",
        config=True,
        help="""
        A filepath to the location of saml settings required for python3-saml.
        Contents of this directory should include settings.json,
        advanced_settings.json, and a cert/ directory if applicable
        """,
    )

    cache_spec = Dict(
        {"type": "disabled", "client": None, "client_kwargs": None},
        config=True,
        help="""
        Specifications for the session cache. Defaults to disabled.

        Allowed values for type = {'in-memory', 'disabled', 'redis'}
        """,
    )

    idp_logout = Bool(
        True,
        config=True,
        help="""
        If set to true, upon logout, will redirect to the IdP single logout URL. If not,
        it'll just clear the cookies defined in "session_cookies".
        """,
    )

    unencrypted_logout = Bool(
        False,
        config=True,
        help="""
        Will do a basic redirect to the single logout URL. Note: setting this to True will
        negate all properties defined within self.logout_kwargs
        """
    )

    logout_kwargs = Dict(
        {},
        config=True,
        help="""
        Extra keyword arguments you can pass to OneLogin's auth class' "logout" method

        If a live cache is specified in cache_spec (e.g. like an in-memory cache), then
        arguments: "name_id" and "session_index" are automatically filled in. Other arguments,
        like return_to, nq, etc. must be provided in a dict here
        
        Example:
        {
            "return_to": "myurl.com/login"
        }

        See https://github.com/onelogin/python3-saml/blob/ba572e24fd3028c0e38c8f9dcd02af46ddcc0870/src/onelogin/saml2/auth.py#L438
        for a full list of all keyword arguments
        """,
    )

    extract_username = Callable(
        help="""
        Extract the username from the attributes returned by the IdP.

        1. the ACSHandler instance if needed
        2. Takes in a dict with the attributes, must return a
        username as a string
        """,
        config=True,
    )

    login_service = Unicode(
        os.environ.get("LOGIN_SERVICE", "SSO"),
        config=True,
        help="""
        Hosted domain string, e.g. your IdP
        """,
    )

    @validate("saml_settings_path")
    def _valid_saml_settings_path(self, proposed):
        proposed_path = proposed["value"]

        # error check
        self._saml_settings_path_exists(proposed_path)
        self._settings_files_exist(proposed_path)

        return proposed_path

    def _saml_settings_path_exists(self, path):
        # error checks
        if not os.path.exists(path):
            raise NotADirectoryError(
                f"Could not locate saml \
                settings path at {path}"
            )

    def _settings_files_exist(self, path):
        dir_contents = os.listdir(path)

        files_to_check = ["settings.json", "advanced_settings.json"]

        for f in files_to_check:
            if f not in dir_contents:
                raise FileNotFoundError(
                    f"Could not locate {f} \
                    in saml settings path. Path = {path}, \
                    contents = {dir_contents}"
                )

    def login_url(self, base_url):
        return url_path_join(base_url, "saml_login")

    def authenticate(self, handler, data):
        return data["name"]

    def _configure_handlers(self):
        self.login_handler.saml_settings_path = self.saml_settings_path

        self.metadata_handler.saml_settings_path = self.saml_settings_path

        self.acs_handler.saml_settings_path = self.saml_settings_path
        self.acs_handler.extract_username = self.extract_username

        self.logout_handler.saml_settings_path = self.saml_settings_path
        self.logout_handler.logout_kwargs = self.logout_kwargs
        self.logout_handler.idp_logout = self.idp_logout
        self.logout_handler.session_cookie_names = self.session_cookie_names
        self.logout_handler.unencrypted_logout = self.unencrypted_logout

    def _setup_cache(self):
        try:
            # test that the cache has been registered
            cache.get()
        except cache.CacheError:
            # if not create it
            created_cache = cache.create(self.cache_spec)

            cache.register(created_cache)

    def get_handlers(self, app):
        self._setup_cache()
        self._configure_handlers()

        return [
            (r"/saml_login", self.login_handler),
            (r"/metadata", self.metadata_handler),
            (r"/acs", self.acs_handler),
            (r"/logout", self.logout_handler),
        ]
