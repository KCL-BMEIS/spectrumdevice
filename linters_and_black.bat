echo 'Formatting code with black...'
black --line-length 120 spectrumdevice
black --line-length 120 tests
black --line-length 120 example_scripts
echo 'Running mypy...'
mypy spectrumdevice
mypy tests
mypy example_scripts
echo 'Running flake8...'
flake8 spectrumdevice
flake8 tests
flake8 example_scripts
