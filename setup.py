from distutils.core import setup
from setuptools import find_packages
import codecs
import os.path


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    """https://packaging.python.org/guides/single-sourcing-package-version/

    Args:
        rel_path (str): relative path of init file with __version__

    Raises:
        RuntimeError: wrong path

    Returns:
        str: version
    """
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


def get_description():
    """https://packaging.python.org/guides/making-a-pypi-friendly-readme/

    Returns:
        str: README file
    """
    this_dir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(this_dir, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
    return long_description


setup(name='jupyterhub_saml_auth',
      version=get_version('jupyterhub_saml_auth/__init__.py'),
      python_requires='>=3.7.0',
      long_description=get_description(),
      long_description_content_type='text/markdown',
      author='Wesley Uykimpang',
      url='https://github.com/ucsd-ets/jupyterhub-saml-auth',
      packages=find_packages(),
      install_requires=['python3-saml'])
