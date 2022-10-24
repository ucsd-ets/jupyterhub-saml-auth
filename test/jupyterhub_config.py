# Configuration file for jupyterhub.
import pwd
import subprocess
import jupyterhub_saml_auth
from os import getenv
from redis import Redis

REDIS_HOST = getenv("REDIS_HOST")
if REDIS_HOST is None:
    raise TypeError("REDIS_HOST environment variable is set to None")

REDIS_PORT = getenv("REDIS_PORT")
if REDIS_PORT is None:
    raise TypeError("REDIS_PORT environment variable is set to None")

REDIS_PASSWORD = getenv("REDIS_PASSWORD")
if REDIS_PASSWORD is None:
    raise TypeError("REDIS_PASSWORD environment variable is set to None")

redis_client = Redis
redis_client_kwargs = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "password": REDIS_PASSWORD,
    "decode_responses": True,
}


def extract_username(acs_handler, attributes):
    email = attributes["email"][0]
    username = email.split("@")[0]
    return username


c.SAMLAuthenticator.saml_settings_path = "/app/etc"
c.SAMLAuthenticator.session_cookie_names = {"PHPSESSIDIDP", "SimpleSAMLAuthTokenIdp"}
c.SAMLAuthenticator.extract_username = extract_username
c.SAMLAuthenticator.cache_spec = {
    "disabled": False,
    "type": "redis",
    "client": redis_client,
    "client_kwargs": redis_client_kwargs,
}

c.JupyterHub.authenticator_class = "jupyterhub_saml_auth.SAMLAuthenticator"


def pre_spawn_hook(spawner):
    # create the user if it doesnt exist
    username = spawner.user.name
    try:
        pwd.getpwnam(username)
    except KeyError:
        subprocess.check_call(["useradd", "-ms", "/bin/bash", username])


c.Spawner.pre_spawn_hook = pre_spawn_hook
