#!/bin/bash
# Ensure inotifywait is installed (usually via inotify-tools on Linux)
# For example, on Debian/Ubuntu: sudo apt-get install inotify-tools

WATCH_FILES="conftest.py models.py test_db_crud.py test_db_exceptions.py"

while true; do
    inotifywait -e modify $WATCH_FILES
    clear
    pytest -s
done
