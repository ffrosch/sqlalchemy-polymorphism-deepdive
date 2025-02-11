#!/bin/bash
# Ensure inotifywait is installed (usually via inotify-tools on Linux)
# For example, on Debian/Ubuntu: sudo apt-get install inotify-tools

WATCH_FILES="models.py test.py"

while true; do
    inotifywait -e modify $WATCH_FILES
    clear
    pytest
done
