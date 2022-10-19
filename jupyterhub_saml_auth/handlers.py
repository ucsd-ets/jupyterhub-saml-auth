from jupyterhub.handlers import LoginHandler, BaseHandler, LogoutHandler
from onelogin.saml2.auth import OneLogin_Saml2_Auth
import tornado
from tornado.log import app_log
import tornado.web
import os
import logging
from .cache import InMemoryCache, SessionEntry

__all__ = [
    'MetadataHandler',
    'SamlLoginHandler',
    'SamlLogoutHandler',
    'ACSHandler'
]

# FIXME abstract this out
cache = InMemoryCache()


def format_request(request):
    dataDict = {}
    for key in request.arguments:
        dataDict[key] = request.arguments[key][0].decode('utf-8')

    # the request may use https, however, request.protocol may interpret it
    # as http. Have an environment variable to override this at
    # the app level in case this happens
    https = 'off'
    if os.environ.get('SAML_HTTPS_OVERRIDE') or request.protocol == 'https':
        https = 'on'

    result = {
        'https': https,
        'http_host': tornado.httputil.split_host_and_port(request.host)[0],
        'script_name': request.path,
        'server_port': tornado.httputil.split_host_and_port(request.host)[1],
        'get_data': dataDict,
        'post_data': dataDict,
        'query_string': request.query
    }

    return result


class BaseHandlerMixin:

    @property
    def saml_settings_path(self):
        return self._saml_settings_path

    @saml_settings_path.setter
    def saml_settings_path(self, path):
        self._saml_settings_path_exists(path)
        self._settings_files_exist(path)

        self._saml_settings_path = path

    def _saml_settings_path_exists(self, path):
        # error checks
        if not os.path.isdir(path):
            raise NotADirectoryError(f'Could not locate \
                saml settings path at {path}')

    def _settings_files_exist(self, path):
        dir_contents = os.listdir(path)

        files_to_check = ['settings.json', 'advanced_settings.json']

        for f in files_to_check:
            if f not in dir_contents:
                raise FileNotFoundError(f'Could not locate {f} in saml \
                    settings path. Path = {path}, contents \
                    = {dir_contents}')


class MetadataHandler(BaseHandler, BaseHandlerMixin):

    def get(self):
        request = format_request(self.request)
        auth = OneLogin_Saml2_Auth(
            request,
            custom_base_path=self.saml_settings_path
        )
        saml_settings = auth.get_settings()
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)

        if len(errors) == 0:
            self.set_header('Content-Type', 'text/xml')
            self.write(metadata)
        else:
            app_log.error(f'Could not serve metadata. Errors = {errors}')
            self.write(', '.join(errors))


class SamlLoginHandler(LoginHandler, BaseHandlerMixin):
    async def get(self):
        request = format_request(self.request)
        auth = OneLogin_Saml2_Auth(
            request,
            custom_base_path=self.saml_settings_path
        )

        return_to = f'{self.request.host}/acs'
        return self.redirect(auth.login(return_to))


class SamlLogoutHandler(LogoutHandler, BaseHandlerMixin):

    @property
    def session_cookie_names(self) -> set:
        try:
            return self._session_cookie_names
        except AttributeError:
            return {}

    @session_cookie_names.setter
    def session_cookie_names(self, cookies):
        if not isinstance(cookies, set):
            raise TypeError(f'session_cookie_names must \
                be a set, not {type(cookies)}')
        self._session_cookie_names = list(cookies)

    @property
    def return_to(self) -> str:
        try:
            return self._return_to
        except AttributeError:
            return None

    @return_to.setter
    def return_to(self, return_to: str):
        if not isinstance(return_to, str):
            raise AttributeError(
                f"return_to must be an str, not = {type(return_to)}")

        self._return_to = return_to

    async def default_handle_logout(self):
        """The default logout action
        Optionally cleans up servers, clears cookies, increments logout counter
        Cleaning up servers can be prevented by setting shutdown_on_logout to
        False.
        """
        user = self.current_user
        username = user.name
        if user:
            if self.shutdown_on_logout:
                await self._shutdown_servers(user)

            self._backend_logout_cleanup(user.name)
            await self.slo_logout(username)

    async def slo_logout(self, username: str):
        for cookie in self.session_cookie_names:
            self.clear_cookie(cookie)

        request = format_request(self.request)
        auth = OneLogin_Saml2_Auth(
            request,
            custom_base_path=self.saml_settings_path
        )

        user_entry = cache.get(username)
        cache.remove(username)
        return self.redirect(auth.logout(name_id=user_entry.name_id, session_index=user_entry.session_index))


class ACSHandler(BaseHandler, BaseHandlerMixin):
    """Assertion consumer service (ACS) handler.  This handler checks the data
    received via a POST request from a SAML server within the SAML workflow. 
    https://goteleport.com/blog/how-saml-authentication-works/
    """
    async def post(self):
        request = format_request(self.request)
        auth = OneLogin_Saml2_Auth(
            request,
            custom_base_path=self.saml_settings_path
        )

        auth.process_response()

        errors = auth.get_errors()

        if len(errors) != 0:
            app_log.error(f'SAML authentication error. Errors = {errors}')
            raise tornado.web.HTTPError(500)

        if not auth.is_authenticated():
            app_log.error('SAML User is not authenticated!')
            raise tornado.web.HTTPError(401)

        user_data = auth.get_attributes()
        username = self.extract_username(user_data)

        # add the user to the cache
        session_entry = SessionEntry(
            name_id=auth.get_nameid(),
            saml_attrs=auth.get_attributes(),
            session_index=auth.get_session_index()
        )

        cache.upsert(username, session_entry)

        user = await self.login_user({'name': username})
        if user is None:
            app_log.error(f'Could not log in user via jupyterhub. \
                username = {username}')

            raise tornado.web.HTTPError(403)
        self.redirect(self.get_next_url(user))
