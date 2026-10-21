#!/bin/sh
set -eu
python -m pip install pip-tools==7.6.2
pip-compile --generate-hashes --output-file=requirements.lock requirements.txt
pip-compile --generate-hashes --output-file=requirements-dev.lock requirements-dev.txt