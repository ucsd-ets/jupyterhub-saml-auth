from jupyterhub.auth import Authenticator
from traitlets import Unicode, validate, Set, Callable
import os

from .handlers import (
    ACSHandler,
    MetadataHandler,
    SamlLoginHandler,
    SamlLogoutHandler,
)


class SAMLAuthenticator(Authenticator):

    acs_handler = ACSHandler
    metadata_handler = MetadataHandler
    login_handler = SamlLoginHandler
    logout_handler = SamlLogoutHandler

    session_cookie_names = Set(
        help='''
        Cookie names for managing SAML session that would be cleared upon
        logout
        ''',
        config=True
    )

    saml_settings_path = Unicode(
        default_value='/etc/saml',
        config=True,
        help='''
        A filepath to the location of saml settings required for python3-saml.
        Contents of this directory should include settings.json,
        advanced_settings.json, and a cert/ directory if applicable
        '''
    )

    extract_username = Callable(
        help='''
        Extract the username from the attributes returned by the IdP.

        1. the ACSHandler instance if needed
        2. Takes in a dict with the attributes, must return a
        username as a string
        ''',
        config=True
    )

    @validate('saml_settings_path')
    def _valid_saml_settings_path(self, proposed):
        proposed_path = proposed['value']

        # error check
        self._saml_settings_path_exists(proposed_path)
        self._settings_files_exist(proposed_path)

        return proposed_path

    def _saml_settings_path_exists(self, path):
        # error checks
        if not os.path.exists(path):
            raise NotADirectoryError(f'Could not locate saml \
                settings path at {path}')

    def _settings_files_exist(self, path):
        dir_contents = os.listdir(path)

        files_to_check = ['settings.json', 'advanced_settings.json']

        for f in files_to_check:
            if f not in dir_contents:
                raise FileNotFoundError(f'Could not locate {f} \
                    in saml settings path. Path = {path}, \
                    contents = {dir_contents}')

    def authenticate(self, handler, data):
        return data['name']

    def configure_handlers(self):
        self.login_handler.saml_settings_path = self.saml_settings_path
        self.metadata_handler.saml_settings_path = self.saml_settings_path
        self.acs_handler.saml_settings_path = self.saml_settings_path
        self.logout_handler.saml_settings = self.saml_settings_path

        self.logout_handler.session_cookie_names = self.session_cookie_names
        self.acs_handler.extract_username = self.extract_username

    def get_handlers(self, app):
        self.configure_handlers()

        return [
            (r'/saml_login', self.login_handler),
            (r'/metadata', self.metadata_handler),
            (r'/acs', self.acs_handler),
            (r'/logout', self.logout_handler)
        ]