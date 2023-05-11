from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
import time
import pytest
import os
import redis
from dotenv import load_dotenv
from redis.commands.json.path import Path as RedisJsonPath
from jupyterhub_saml_auth.cache import SessionEntry

SECONDS_WAIT = 20
load_dotenv()

@pytest.fixture
def setup_docker_env(request):
    # sleep to ensure that previous docker compose calls have completed
    time.sleep(3)

    # set environment variables before test
    for k, v in request.param.items():
        os.environ[k] = v

    os.system("docker compose up -d")

    yield

    os.system("docker compose down")
    for k, v in request.param.items():
        del os.environ[k]

@pytest.fixture()
def driver_options(pytestconfig):
    browser = pytestconfig.getoption("browser")
    headless = pytestconfig.getoption("headless")
    if browser == "firefox":
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        return (webdriver.Firefox, options)
    elif browser == "chrome":
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        return (webdriver.Chrome, options)

    else:
        raise Exception(f"No browser option available for {browser}")

@pytest.fixture()
def driver(driver_options):
    driver_cls, selected_options = driver_options
    driver = driver_cls(options=selected_options)
    yield driver

    driver.quit()

def login_test(driver):
    driver.get("http://localhost:8000/hub/saml_login")
    wait_for_element(driver, By.ID, "username").send_keys("user1")

    wait_for_element(driver, By.ID, "password").send_keys("user1pass")

    wait_for_element(driver, By.CSS_SELECTOR, ".btn").click()

    # allow some time for server to spawn
    time.sleep(5)

    assert driver.current_url == "http://localhost:8000/user/user1/tree/?"

    return driver


def logout_test(driver):
    # check cookies set
    cookies_names_to_check = {"SimpleSAMLAuthTokenIdp", "jupyterhub-session-id"}
    current_cookies = set(map(lambda cookie: cookie["name"], driver.get_cookies()))
    assert cookies_names_to_check.issubset(current_cookies), current_cookies

    # logout
    wait_for_element(driver, By.ID, "logout").click()
    cookies = driver.get_cookies()
    for cookie in cookies:
        assert cookie["name"] not in cookies_names_to_check, cookie["name"]

    # SLO logout, confirm that clicking login again is logged out of idp
    driver.get("http://localhost:8000/hub/saml_login")
    assert driver.current_url.startswith("http://localhost:8080")

    return driver


def wait_for_element(driver, selector, selector_value) -> WebDriverWait:
    return WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.element_to_be_clickable((selector, selector_value))
    )


@pytest.mark.parametrize("setup_docker_env", [{}], indirect=True)
def test_defaults(setup_docker_env, driver):
    """Default settings

    cache_spec = {'type': 'disabled'}
    """
    driver = login_test(driver)
    logout_test(driver)

@pytest.mark.parametrize("setup_docker_env", [{"TEST_ENV": "redis"}], indirect=True)
def test_redis_cache(setup_docker_env, driver):
    r = redis.Redis(
        host="localhost",
        port=os.getenv("REDIS_PORT"),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
    )
    assert r.ping()

    driver = login_test(driver)

    # check that the user has been registered in redis
    session_args = r.json().get("user1", RedisJsonPath.root_path())
    assert session_args
    session_entry = SessionEntry(**session_args)
    for field, value in session_entry.__dataclass_fields__.items():
        assert value, (field, value)

    logout_test(driver)

