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

SECONDS_WAIT = 60
load_dotenv()
browser = None

@pytest.fixture
def setup_docker_env(request):
    # set environment variables before test
    for k, v in request.param.items():
        os.environ[k] = v

    os.system("docker compose --verbose up -d")

    yield

    os.system("docker compose --verbose down")
    for k, v in request.param.items():
        del os.environ[k]

@pytest.fixture()
def driver_options(pytestconfig):
    global browser
    browser = pytestconfig.getoption("browser")
    headless = pytestconfig.getoption("headless")
    if browser == "firefox":
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        options.page_load_strategy = 'eager'
        return (webdriver.Firefox, options)
    elif browser == "chrome":
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.page_load_strategy = 'eager'
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
    get_page_retry(driver, "http://localhost:8000/hub/saml_login")
    #driver.get("http://localhost:8000/hub/saml_login")
    
    wait_for_element(driver, By.ID, "username").send_keys("user1")

    wait_for_element(driver, By.ID, "password").send_keys("user1pass")

    wait_for_element(driver, By.CSS_SELECTOR, ".btn").click()

    # Wait for correct URL
    correct_url = "http://localhost:8000/user/user1/tree?"
    result = wait_for_url_match(driver, correct_url)
    
    assert driver.current_url == correct_url
    # assert driver.current_url == "http://localhost:8000/user/user1/tree/?"

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
    #driver.get("http://localhost:8000/hub/saml_login")
    get_page_retry(driver, "http://localhost:8000/hub/saml_login")
    
    assert driver.current_url.startswith("http://localhost:8080")

    return driver

def wait_for_url_match(driver, new_url) -> WebDriverWait:
    isDone = False
    count = 0
    while not isDone:
        if count == 3:
            raise Exception("Exception after " + str(count) + " tries...URL not correct?")
            break
        try:
            driver.set_page_load_timeout(SECONDS_WAIT/2)
            element = WebDriverWait(driver, SECONDS_WAIT/2).until(expected_conditions.url_to_be((new_url)))
            isDone = True
        except:
            # Selenium may not have loaded this page yet
            # On each fail, refresh the page and try again...
            print("Exception encountered on attempt " + str(count) + ". Trying again...")
            count = refresh_driver(driver, count)
    time.sleep(1)
    return element

def wait_for_element(driver, selector, selector_value) -> WebDriverWait:
    isDone = False
    count = 0
    while not isDone:
        if count == 10:
            raise Exception("TimeoutException after " + str(count) + " tries...Is element present?")
            break
        try:
            driver.set_page_load_timeout(SECONDS_WAIT)
            element = WebDriverWait(driver, SECONDS_WAIT).until(expected_conditions.element_to_be_clickable((selector, selector_value)))
            isDone = True
        except:
            # Selenium often randomly fails with TimeoutException
            # On each fail, refresh the page and try again...
            print("TimeoutException encountered on attempt " + str(count) + ". Trying again...")
            count = refresh_driver(driver, count)
    time.sleep(1)
    return element

def get_page_retry(driver, url):
    isDone = False
    count = 0
    while not isDone:
        if count == 5:
            raise Exception("Failed to get page following " + str(count) + " ConnectionReset exceptions...is docker online?")
            break
        try:
            driver.set_page_load_timeout(SECONDS_WAIT)
            page = driver.get(url)
            isDone = True
        except:
            # driver.get(url) may fail with ConnectionReset
            # On each fail, refresh and try again...
            print("ConnectionReset encountered on attempt " + str(count) + ". Trying again...")
            count = refresh_driver(driver, count)
    time.sleep(1)
    return page

def refresh_driver(driver, count):
    time.sleep(7)
    if (browser != "firefox"):
        driver.refresh()
    count += 1
    return count

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

