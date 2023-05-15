from jupyterhub.handlers import LoginHandler, BaseHandler, LogoutHandler
from onelogin.saml2.auth import OneLogin_Saml2_Auth
import tornado
from tornado.log import app_log
import tornado.web
import os
from . import cache

__all__ = ["MetadataHandler", "SamlLoginHandler", "SamlLogoutHandler", "ACSHandler"]


def format_request(request, https_override=False):
    dataDict = {}
    for key in request.arguments:
        dataDict[key] = request.arguments[key][0].decode("utf-8")

    # the request may use https, however, request.protocol may interpret it
    # as http. Have an environment variable to override this at
    # the app level in case this happens
    https = "off"
    if (
        os.environ.get("SAML_HTTPS_OVERRIDE")
        or request.protocol == "https"
        or https_override
    ):
        https = "on"

    result = {
        "https": https,
        "http_host": tornado.httputil.split_host_and_port(request.host)[0],
        "script_name": request.path,
        "server_port": tornado.httputil.split_host_and_port(request.host)[1],
        "get_data": dataDict,
        "post_data": dataDict,
        "query_string": request.query,
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

    @property
    def session_cache(self):
        try:
            return self._session_cache.get()
        except AttributeError:
            self._session_cache = cache
            return self._session_cache.get()

    @session_cache.setter
    def session_cache(self, session_cache):
        self._session_cache = session_cache

    @property
    def https_override(self):
        return self._https_override

    @https_override.setter
    def https_override(self, https_override):
        self._https_override = https_override

    def _saml_settings_path_exists(self, path):
        # error checks
        if not os.path.isdir(path):
            raise NotADirectoryError(
                f"Could not locate \
                saml settings path at {path}"
            )

    def _settings_files_exist(self, path):
        dir_contents = os.listdir(path)

        files_to_check = ["settings.json", "advanced_settings.json"]

        for f in files_to_check:
            if f not in dir_contents:
                raise FileNotFoundError(
                    f"Could not locate {f} in saml \
                    settings path. Path = {path}, contents \
                    = {dir_contents}"
                )

    def setup_auth(self) -> OneLogin_Saml2_Auth:
        request = format_request(self.request, self.https_override)
        onelogin_auth = OneLogin_Saml2_Auth(
            request, custom_base_path=self.saml_settings_path
        )
        return onelogin_auth

    def check_xsrf_cookie(self):
        # no xsrf check needed here
        return


class MetadataHandler(BaseHandlerMixin, BaseHandler):
    def get(self):
        auth = self.setup_auth()
        saml_settings = auth.get_settings()
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)

        if len(errors) == 0:
            self.set_header("Content-Type", "text/xml")
            self.write(metadata)
        else:
            app_log.error(f"Could not serve metadata. Errors = {errors}")
            self.write(", ".join(errors))


class SamlLoginHandler(BaseHandlerMixin, LoginHandler):
    async def get(self):
        auth = self.setup_auth()
        return_to = f"{self.request.host}/acs"
        return self.redirect(auth.login(return_to))


class SamlLogoutHandler(BaseHandlerMixin, LogoutHandler):
    @property
    def logout_kwargs(self):
        return self._logout_kwargs

    @logout_kwargs.setter
    def logout_kwargs(self, logout_kwargs: dict):
        self._logout_kwargs = logout_kwargs

    @property
    def session_cookie_names(self) -> set:
        try:
            return self._session_cookie_names
        except AttributeError:
            return {}

    @session_cookie_names.setter
    def session_cookie_names(self, cookies):
        if not isinstance(cookies, set):
            raise TypeError(
                f"session_cookie_names must \
                be a set, not {type(cookies)}"
            )
        self._session_cookie_names = list(cookies)

    @property
    def idp_logout(self):
        return self._idp_logout

    @idp_logout.setter
    def idp_logout(self, idp_logout: bool):
        if not isinstance(idp_logout, bool):
            raise AttributeError("idp_logout must be an instance of a bool")

        self._idp_logout = idp_logout

    @property
    def unencrypted_logout(self):
        return self._unencrypted_logout

    @unencrypted_logout.setter
    def unencrypted_logout(self, unencrypted_logout: bool):
        if not isinstance(unencrypted_logout, bool):
            raise AttributeError("You must supply a bool as unencrypted_logout")

        self._unencrypted_logout = unencrypted_logout

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
        auth = self.setup_auth()
        for cookie in self.session_cookie_names:
            self.clear_cookie(cookie)

        user_entry = self.session_cache.get(username)
        self.session_cache.remove(username)

        if self.idp_logout:
            if not self.unencrypted_logout:
                app_log.debug(f"encrypted logout for {username}")
                return self.redirect(
                    auth.logout(
                        name_id=user_entry.name_id,
                        session_index=user_entry.session_index,
                        **self.logout_kwargs,
                    )
                )
            else:
                url = auth.get_slo_url()
                app_log.debug(f"unencrypted redirect to {url} for {username}")
                self.redirect(url, status=307)


class ACSHandler(BaseHandlerMixin, BaseHandler):
    """Assertion consumer service (ACS) handler.  This handler checks the data
    received via a POST request from a SAML server within the SAML workflow.
    https://goteleport.com/blog/how-saml-authentication-works/
    """

    async def post(self):
        auth = self.setup_auth()
        auth.process_response()

        errors = auth.get_errors()

        if len(errors) != 0:
            app_log.error(f"SAML authentication error. Errors = {errors}")
            raise tornado.web.HTTPError(500)

        if not auth.is_authenticated():
            app_log.error("SAML User is not authenticated!")
            raise tornado.web.HTTPError(401)

        user_data = auth.get_attributes()
        username = self.extract_username(user_data)

        # add the user to the cache
        session_entry = cache.SessionEntry(
            name_id=auth.get_nameid(),
            saml_attrs=auth.get_attributes(),
            session_index=auth.get_session_index(),
        )

        self.session_cache.upsert(username, session_entry)

        user = await self.login_user({"name": username})
        if user is None:
            app_log.error(
                f"Could not log in user via jupyterhub. \
                username = {username}"
            )

            raise tornado.web.HTTPError(403)
        self.redirect(self.get_next_url(user))
