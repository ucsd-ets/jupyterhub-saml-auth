from jupyterhub.handlers import LoginHandler, BaseHandler, LogoutHandler
from onelogin.saml2.auth import OneLogin_Saml2_Auth
import tornado
from tornado.log import app_log
import tornado.web
import os
import logging

__all__ = [
    'MetadataHandler',
    'SamlLoginHandler',
    'SamlLogoutHandler',
    'ACSHandler',
    'SLSHandler'
]

logging.basicConfig(filename="log.txt",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

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
    async def handle_logout(self):
        logging.info("logout handler")
        request = format_request(self.request)
        auth = OneLogin_Saml2_Auth(
            request,
            custom_base_path=self.saml_settings_path
        )
        logging.info(request)
        delete_session_callback = lambda: self.request.clear()
        logging.info("cleared request")
        try:
            url = auth.process_slo(delete_session_cb=delete_session_callback)
        except Exception as e:
            logging.error(str(e))
        logging.info("processed SLO")
        errors = auth.get_errors()
        if len(errors) == 0:
            if url is not None:
                return self.redirect(url)
        else:
            app_log.error(("Error when processing SLO: %s %s" % (', '.join(errors), auth.get_last_error_reason())))
            raise tornado.web.HTTPError(500)


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

        user = await self.login_user({'name': username})
        if user is None:
            app_log.error(f'Could not log in user via jupyterhub. \
                username = {username}')

            raise tornado.web.HTTPError(403)
        self.redirect(self.get_next_url(user))


class SLSHandler(BaseHandler, BaseHandlerMixin):
    """Single logout service (SLS) handler.  This handler logs out a session
    when it recieves a POST request to logout.
    """
    async def post(self):
        # request = format_request(self.request)
        # auth = OneLogin_Saml2_Auth(
        #     request,
        #     custom_base_path=self.saml_settings_path
        # )
        # delete_session_callback = lambda: self.request.clear()
        # url = auth.process_slo(delete_session_cb=delete_session_callback)
        # errors = auth.get_errors()
        # if len(errors) == 0:
        #     if url is not None:
        #         return self.redirect(url)
        # else:
        #     app_log.error(("Error when processing SLO: %s %s" % (', '.join(errors), auth.get_last_error_reason())))
        #     raise tornado.web.HTTPError(500)
        pass
