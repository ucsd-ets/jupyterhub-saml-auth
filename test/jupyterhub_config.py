# Configuration file for jupyterhub.
import pwd
import subprocess


def extract_username(acs_handler, attributes):
    email = attributes['email'][0]
    username = email.split('@')[0]
    return username


c.SAMLAuthenticator.saml_settings_path = '/app/etc'
c.SAMLAuthenticator.session_cookie_names = {
    'PHPSESSIDIDP', 'SimpleSAMLAuthTokenIdp'}
c.SAMLAuthenticator.extract_username = extract_username

c.JupyterHub.authenticator_class = 'jupyterhub_saml_auth.SAMLAuthenticator'


def pre_spawn_hook(spawner):
    # create the user if it doesnt exist
    username = spawner.user.name
    try:
        pwd.getpwnam(username)
    except KeyError:
        subprocess.check_call(['useradd', '-ms', '/bin/bash', username])


c.Spawner.pre_spawn_hook = pre_spawn_hook
