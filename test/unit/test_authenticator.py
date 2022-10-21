from jupyterhub_saml_auth.authenticator import SAMLAuthenticator
from jupyterhub_saml_auth.handlers import session_cache
import pytest


@pytest.fixture()
def mock_saml_authenticator():
    return SAMLAuthenticator()


def test_login_url_sets(mock_saml_authenticator):
    assert '/hub/saml_login' == mock_saml_authenticator.login_url('/hub')


def test_login_service_sets(mock_saml_authenticator):
    assert mock_saml_authenticator.login_service == 'SSO'


# def test_set_cache_spec(mock_saml_authenticator):
#     # check defaults
#     print(mock_saml_authenticator.cache_spec)
#     assert session_cache