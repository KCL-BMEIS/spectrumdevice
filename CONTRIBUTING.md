# Contributing to spectrumdevice

`spectrumdevice` is a very new project that's only been tested on the devices we have in our lab. It is certain users 
will encounter issues and missing features that need addressing, so we welcome contributions — thank you for 
considering helping out.

## Bug reports and feature requests

Raise an issue in the GitHub repository using one of the provided templates.

## Submitting a contribution

### Overview
To submit a contribution you'll need to:
- Fork the GitHub project
- Clone your fork of the repository
- Install the development and testing dependencies to your Python environment with `pip install .[dev,test]`
- Create a new branch. Its name should begin with the issue number you're addressing, e.g. 123-fix-connection-bug
- Make your changes, keeping your branch rebased on top of the main branch
- Push the new branch to your fork on GitHub
- Open a pull request to merge it into the main branch of the original repository.

### Linters
Before a pull request can be reviewed, it must successfully pass Flake8 linting, Mypy type checking and Black 
formatting. You should run these checks on your local machine before pushing your branch. A shell script 
`linters_and_black.bat` which runs the checks for you (and should work on Windows, Linux and macOS) is included in 
the repository. This script will automatically reformat your code using Python Black.

### Tests
Any new features should have tests written for them in the `tests` package. You should run tests locally using `pytest`
before pushing your branch. These tests are primarily intended to be run on mock hardware during CI, but you can
temporarily configure them in `tests/configuration.py` to run on real hardware on your local system when required. 
Please let us know in the pull request if you have successfully run tests on hardware.

### Documentation
Once your branch is merged into the main branch, documentation will be automatically generated from README.md and the
Python docstrings using [pdoc](https://pdoc.dev). Any new functions, classes and methods — particularly those that form 
part of  the external API — should therefore include docstrings (in NumPy format). You should check that any changes you
have made are reflected well in the documentation by building the docs locally using the `generate_docs.sh`
script, which should work on Linux and macOS. To include the correct version number in your locally-built docs, 
you'll need to first set a `SPECTRUMDEVICE_VERSION` environment variable:
```
export SPECTRUMDEVICE_VERSION='vx.x.x'
source generate_docs.sh
```

### Testing on hardware
We'll accept code into the main branch that has not necessarily been tested on real hardware, as long as it passes the 
unit tests on mock hardware. However, before a release we will endeavour to run all tests on real hardware. This is 
unfortunately only possible to do on the Spectrum devices we have in our lab. If your encounter any problems on your
specific hardware, let us know by raising an issue. If you have regular access to a Spectrum device and would like 
to be involved in pre-release testing, please get in touch.
