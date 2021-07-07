# Jupyterhub SAML Auth

[![image](https://badge.fury.io/py/jupyterhub-saml-auth.svg)](https://pypi.org/project/jupyterhub-saml-auth/)

Authenticate your Jupyterhub users using SAML. This authenticator uses OneLogin's [python3-saml](https://github.com/onelogin/python3-saml) package as a backend API for handling SAML authentication.


## Installation

For now, install via pip and git

```bash
pip install git+https://github.com/ucsd-ets/jupyterhub-saml-auth.git
```

## Configuration

See the `jupyterhub_config.py` example configuration below for how to integrate this package with jupyterhub

```python
def extract_username(acs_handler, attributes):
    email = attributes['email'][0]
    username = email.split('@')[0]
    return username

# The configuration path is for OneLogin's python3-saml package. This directory is where
# settings.json & advanced_settings.json go. See https://github.com/onelogin/python3-saml
# for more info about this
c.SAMLAuthenticator.saml_settings_path = '/app/etc'

# The cookies that your IdP uses for maintaining a login session. These will be cleared
# once the user hits 'logout'
c.SAMLAuthenticator.session_cookie_names = {'PHPSESSIDIDP', 'SimpleSAMLAuthTokenIdp'}

# Function that extracts the username from the SAML attributes.
c.SAMLAuthenticator.extract_username = extract_username

# register the SAML authenticator with jupyterhub
c.JupyterHub.authenticator_class = 'jupyterhub_saml_auth.SAMLAuthenticator'
```

## Development

### Prerequisite software

- docker
- docker compose
- python3
- Firefox or Chrome

### Create a development environment

```bash
# at project root
python3 -m venv .
source bin/activate
pip install -r requirements.txt

# OPTIONAL, install package if developing source code
pip install -e .
pytest test/unit # run the unit tests

```

#### Test the authentication process

The acceptance test starts the application as a Docker container. Start the containers with `docker compose up -d` prior to running the acceptance test with the command `pytest test/test_acceptance.py`. See `conftest.py` for a list of command line switches/flags to run the acceptance tests.

### Kill your docker environment

To kill the docker containers, run the command `docker compose down` at the project root.

## References

https://github.com/onelogin/python3-saml

https://goteleport.com/blog/how-saml-authentication-works/

https://medium.com/@BoweiHan/elijd-single-sign-on-saml-and-single-logout-624efd5a224

https://medium.com/disney-streaming/setup-a-single-sign-on-saml-test-environment-with-docker-and-nodejs-c53fc1a984c9