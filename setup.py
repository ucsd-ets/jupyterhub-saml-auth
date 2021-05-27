from distutils.core import setup
from setuptools import find_packages
import codecs
import os.path
import sys

# https://packaging.python.org/guides/single-sourcing-package-version/
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

setup(name='jupyterhub_saml_auth',
      version=get_version('jupyterhub_saml_auth/__init__.py'),
      python_requires='>=3.6.5',
      description='',
      author='',
      author_email='',
      url='',
      packages=find_packages(),
     )