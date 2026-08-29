#!/bin/bash
cd "$(dirname "$0")/.."
git pull --quiet
python -m manga_translator $@