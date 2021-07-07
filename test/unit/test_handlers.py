from tornado.httputil import HTTPServerRequest
from jupyterhub_saml_auth.handlers import get_request
import pytest

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

def test_get_request_http(mock_request):
    res = get_request(mock_request)
    assert res['https'] == 'off'

def test_get_reqwuest_https(mock_request):
    mock_request.protocol = 'https'
    res = get_request(mock_request)
    assert res['https'] == 'on'
