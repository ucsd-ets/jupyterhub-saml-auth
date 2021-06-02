# Jupyterhub SAML Auth

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

# The configuration path is for OneLogin's python3-saml package
c.SAMLAuthenticator.saml_settings_path = '/app/etc'

# The cookies that your IdP uses for maintaining a login session. These will be cleared
# once the user hits 'logout'
c.SAMLAuthenticator.session_cookie_names = {'PHPSESSIDIDP', 'SimpleSAMLAuthTokenIdp'}

# Function that pulls the username from the SAML attributes.
c.SAMLAuthenticator.extract_username = extract_username

# register the SAML authenticator
c.JupyterHub.authenticator_class = 'jupyterhub_saml_auth.authenticator.SAMLAuthenticator'
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

# start the docker containers
docker compose up -d
```

### Test the authentication process

The application and IdP runs as docker containers and bind to ports: 8000, 8443, and 8080. You can navigate to `localhost:8000` in your browser to begin testing and to login via SAML, navigate to `localhost:8000/hub/saml_login`. The user registered in the IdP is `user1` with password `user1pass`.

### Kill your docker environment

To kill the docker containers, run the command `docker compose down` at the project root.

### Run the automated tests

The commands below kick off a selenium end-to-end test that will test the full authentication and logout process.

```bash
# at project root
pytest tests --browser <firefox|chrome> # defaults to firefox
pytest tests --headless # no browser will be opened if passed --headless flag
```

## References

https://github.com/onelogin/python3-saml

https://goteleport.com/blog/how-saml-authentication-works/

https://medium.com/@BoweiHan/elijd-single-sign-on-saml-and-single-logout-624efd5a224

https://medium.com/disney-streaming/setup-a-single-sign-on-saml-test-environment-with-docker-and-nodejs-c53fc1a984c9