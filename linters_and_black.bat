black --line-length 120 pyspecde
black --line-length 120 tests
black --line-length 120 example_scripts
mypy pyspecde
mypy tests
mypy example_scripts
flake8 pyspecde
flake8 tests
flake8 example_scripts
