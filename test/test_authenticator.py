from jupyterhub_saml_auth.authenticator import SAMLAuthenticator
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
            options.set_headless()
        driver = webdriver.Firefox(options=options)
    elif browser == 'chrome':
        options = webdriver.ChromeOptions()
        if headless:
            options.set_headless()
        driver = webdriver.Chrome(options=options)
    
    else:
        raise Exception(f'No browser option available for {browser}')

    yield driver
    
    driver.quit()

def test_authentication(driver):
    driver.get('http://localhost:8000/hub/saml_login')
    WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.element_to_be_clickable(
            (By.ID, 'username'))
    ).send_keys('user1')
    
    WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.element_to_be_clickable(
            (By.ID, 'password'))
    ).send_keys('user1pass')

    WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.element_to_be_clickable(
            (By.CSS_SELECTOR, '.btn'))
    ).click()
    
    time.sleep(5) # allow some time for server to spawn
    
    assert driver.current_url == 'http://localhost:8000/user/user1/tree?'
    
    cookies_names_to_check = {'PHPSESSIDIDP', 'SimpleSAMLAuthTokenIdp', 'jupyterhub-session-id'}
    current_cookies = set(map(lambda cookie: cookie['name'], driver.get_cookies()))
    assert cookies_names_to_check.issubset(current_cookies)

    ### logout
    WebDriverWait(driver, SECONDS_WAIT).until(
        expected_conditions.element_to_be_clickable(
            (By.ID, 'logout'))
    ).click()
    
    assert driver.get_cookies() == []