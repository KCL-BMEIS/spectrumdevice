import setuptools


if __name__ == "__main__":
    try:
        import versioneer
        setuptools.setup(version=versioneer.get_version(), cmdclass=versioneer.get_cmdclass())
    except ImportError:
        setuptools.setup()

