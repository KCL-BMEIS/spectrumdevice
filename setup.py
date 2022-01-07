import setuptools
from spectrumdevice._version import get_versions
__version__ = get_versions()['version']


if __name__ == "__main__":
    setuptools.setup(version=get_versions()['version'])
