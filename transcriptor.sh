#!/bin/bash

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Run the application
python transcriptor.py 