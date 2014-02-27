#!/bin/bash
set -e
set -E
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
rm -rf dist
rm -rf build
rm -rf *.egg-info
find . -iname '*.pyc' | xargs -I{} rm -f {}
