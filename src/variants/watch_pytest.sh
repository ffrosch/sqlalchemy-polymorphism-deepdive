#!/bin/bash
# This script uses inotifywait to monitor improved.py and test_improved.py for modifications.

# Ensure inotifywait is installed (usually via inotify-tools on Linux)
# For example, on Debian/Ubuntu: sudo apt-get install inotify-tools

WATCH_FILES="improved.py test_improved.py"

while true; do
    inotifywait -e modify $WATCH_FILES
    clear
    pytest
done
