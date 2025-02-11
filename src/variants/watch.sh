#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <file_to_watch>"
    exit 1
fi

FILE_TO_WATCH=$1

while true; do
    inotifywait -e modify "$FILE_TO_WATCH"
    clear
    pytest
done
