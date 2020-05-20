#!/bin/sh
set -e
set -x
pytest \
    --failed-first \
    --new-first \
    --exitfirst \
    --flake8 \
    --cov=src \
    --cov-branch \
    --no-cov-on-fail $@
