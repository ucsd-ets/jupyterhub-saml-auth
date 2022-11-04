import codecs
import os.path
from sys import version_info

from setuptools import find_packages, setup

MIN_PYTHON_VERSION = f"{version_info.major}.{version_info.minor}.0"


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

def get_long_description():
    with open("README.md", "r", encoding="utf-8") as readme_file:
        long_description = readme_file.read()
    return long_description


setup(name='jupyterhub_saml_auth',
    version=get_version('jupyterhub_saml_auth/__init__.py'),
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Wesley Uykimpang',
    url='https://github.com/ucsd-ets/jupyterhub-saml-auth',
    packages=find_packages(),
    classifiers=[
        f"Programming Language :: Python :: {MIN_PYTHON_VERSION}",
        "Operating System :: OS Independent",
    ],
    python_requires=f">={MIN_PYTHON_VERSION}",
    install_requires=[
        'python3-saml',
        'jupyterhub',
        'traitlets>=5.0.0',
        'notebook',
        'redis',
    ],
    extra_requires={
        'kubernetes': [
            'kubernetes',
        ],
        'dev': [
            'python-dotenv',
            'black',
            'flake8',
            'selenium',
        ]
    }
)
