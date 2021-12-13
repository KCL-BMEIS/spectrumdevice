echo 'Formatting code with black...'
black --line-length 120 pyspecde
black --line-length 120 tests
black --line-length 120 example_scripts
echo 'Running mypy...'
mypy pyspecde
mypy tests
mypy example_scripts
echo 'Running flake8...'
flake8 pyspecde
flake8 tests
flake8 example_scripts
