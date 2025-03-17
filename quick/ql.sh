#!/bin/bash
set -e

python -m main -C config.yml -P mono -O default -R dwt -r -j 3 -A ql -DT -DE
python -m tools.plot
