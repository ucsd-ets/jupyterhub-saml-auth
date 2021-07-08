from jupyterhub_saml_auth.authenticator import SAMLAuthenticator


def test_login_url_sets():
    samlauth = SAMLAuthenticator()
    assert '/hub/saml_login' == samlauth.login_url('/hub')
