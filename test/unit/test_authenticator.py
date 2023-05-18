from jupyterhub_saml_auth.authenticator import SAMLAuthenticator
import pytest


@pytest.fixture()
def mock_saml_authenticator():
    return SAMLAuthenticator()


def test_login_url_sets(mock_saml_authenticator):
    assert "/hub/saml_login" == mock_saml_authenticator.login_url("/hub")


def test_login_service_sets(mock_saml_authenticator):
    assert mock_saml_authenticator.login_service == "SSO"
