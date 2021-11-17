import unittest
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
import time
import pytest

SECONDS_WAIT = 15


@pytest.fixture()
def driver(pytestconfig):
    browser = pytestconfig.getoption("browser")
    headless = pytestconfig.getoption('headless')

    if browser == 'firefox':
        options = webdriver.FirefoxOptions()
        if headless:
            options.headless = True
        driver = webdriver.Firefox(options=options)
    elif browser == 'chrome':
        options = webdriver.ChromeOptions()
        if headless:
            options.headless = True
        driver = webdriver.Chrome(options=options)

    else:
        raise Exception(f'No browser option available for {browser}')

    yield driver

    driver.quit()

def wait_for_element(driver, selector, selector_value) -> WebDriverWait:
    return WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.element_to_be_clickable(
            (selector, selector_value))
    )

def test_authentication(driver):
    driver.get('http://localhost:8000/hub/saml_login')
    wait_for_element(driver, By.ID, 'username').send_keys('user1')

    wait_for_element(driver, By.ID, 'password').send_keys('user1pass')

    wait_for_element(driver, By.CSS_SELECTOR, '.btn').click()

    # allow some time for server to spawn
    time.sleep(5)

    assert driver.current_url == 'http://localhost:8000/user/user1/tree?'

    cookies_names_to_check = {
        'PHPSESSIDIDP',
        'SimpleSAMLAuthTokenIdp',
        'jupyterhub-session-id'
    }
    current_cookies = set(
        map(lambda cookie: cookie['name'], driver.get_cookies())
    )
    assert cookies_names_to_check.issubset(current_cookies)

    # logout
    wait_for_element(driver, By.ID, 'logout').click()

    assert driver.get_cookies() == []
