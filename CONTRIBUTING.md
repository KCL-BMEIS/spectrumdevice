# Contributing to spectrumdevice

Thanks for considering contirbuting to spectrumdevice. It's a very new project that's only been tested on the devices we have in our lab, so its likely users will encounter issues and missing features that need addressing - please let us know!

## Bug reports and feature requests

Raise an issue in the GitHub's repository using one of the templates provided templates.

## Submitting a contribution

### Overview
In short, to submit a contribution you'll need to:
- Clone the repository
- Install the development and testing dependencies to your Python environment with `pip install .[dev,test]`
- Create a new branch starting. Its name shoud begin with the issue number you're addressing, e.g. 123-fix-connection-bug
- Make your changes
- Push the new branch to github and open a pull request

### Linters
Before a pull request can be reviewed, it must succesfully pass Flake8 linting, Mypy type checking and Black formatiing. You should run these checks on your local machine before pushing your branch. A shell script `linters_and_black.bat` (should work on Windows, Linux and MacOS) is included in the repository which runs the checks for you. This will automatically reformat your code using Python Black.

### Tests
Any new features should be tested in the `tests` package. You should run tests locally using `pytest` before pushing your branch. These tests run on mock hardware by default, but you can configure them in `tests/configuration.py` to run on real hardware if necessary.

### Documentation
Once your branch is merged into the main branch , documentation will be automatically generated from README.md and the Python docstrings using [pdoc](https://pdoc.dev). You should check that any changes you have made are reflected well in the documentation by building the docs locally using the `generate_docs.bat` shell script, which should work on Windows, Linux and MacOS.

### Testing on hardware
We'll accept code into the main branch that passes the unit tests on mock harware and that hasn't necessarily been tested on real hardware. However, before a release we will endevour to run all tests on real hardware. This is unfortunately only possible to do on the Spectrum devices we have in our lab. If your encounter any problems on your specific harware, raise an issue.
