echo 'Formatting code with black...'
black --line-length 120 src/spectrumdevice
black --line-length 120 src/tests
black --line-length 120 src/example_scripts
echo 'Running mypy...'
mypy src/spectrumdevice
mypy src/tests
mypy src/example_scripts
echo 'Running flake8...'
flake8 src/spectrumdevice
flake8 src/tests
flake8 src/example_scripts
