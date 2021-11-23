from tornado.httputil import HTTPServerRequest
from jupyterhub_saml_auth.handlers import format_request
import pytest
import os


@pytest.fixture()
def mock_request():
    mock_req = HTTPServerRequest()

    mock_req.protocol = 'http'
    mock_req.host = 'localhost:8000'
    mock_req.method = 'POST'
    mock_req.uri = '/hub/acs'
    mock_req.version = 'HTTP/1.1'
    mock_req.remote_ip = '::ffff:172.21.0.1'

    return mock_req

def test_format_request_http(mock_request):
    res = format_request(mock_request)
    assert res['https'] == 'off'

def test_format_request_https(mock_request):
    mock_request.protocol = 'https'
    res = format_request(mock_request)
    assert res['https'] == 'on'

def test_format_request_https_override(mock_request):
    os.environ['SAML_HTTPS_OVERRIDE'] = 'true'
    res = format_request(mock_request)
    assert res['https'] == 'on'
