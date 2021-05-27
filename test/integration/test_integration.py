import os
import time
import threading
import requests


HOST = 'http://localhost:8000'

def start_jupyterhub():
    config_path = os.path.join(os.getcwd(), 'test', 'integration', 'jupyterhub_config.py')
    os.system(f'jupyterhub -f {config_path}')

def jupyterhub_is_ready(sleep_time=0.5, limit=10):
    tries = 0
    def is_200():
        try:
            is_200 = requests.get(HOST).status_code != 200
            return is_200
        except:
            return False
            
    while not is_200():
        time.sleep(sleep_time)
        tries += 1
        if tries == limit:
            raise Exception('Could not start jupyterhub!')
    return

def test_authenticator_integrates():
    jhub = threading.Thread(target=start_jupyterhub)
    jhub.start()

    # block until jupyterhub is up
    jupyterhub_is_ready()

    