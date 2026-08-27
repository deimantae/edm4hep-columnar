#!/bin/bash

# Script must be sourced so environment changes are kept in the current shell
if [ "${0}" == "${BASH_SOURCE[0]}" ]; then
    echo "ERROR: Set up the environment with:"
    echo "  source setup.sh"
    exit 1
fi

# Find directory containing this script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Remove existing Python settings
unset PYTHONPATH
unset PYTHONHOME

# Create the virtual environment and install dependencies if needed
if [ ! -d "${SCRIPT_DIR}/.venv" ]; then
    echo "----> Creating Python virtual environment..."
    python3 -m venv "${SCRIPT_DIR}/.venv"

    echo "----> Activating Python virtual environment..."
    source "${SCRIPT_DIR}/.venv/bin/activate"

    # Install everything listed in requirements.txt
    echo "----> Installing Python dependencies..."
    python -m pip install -q -r "${SCRIPT_DIR}/requirements.txt"

else
    echo "----> Activating Python virtual environment..."
    source "${SCRIPT_DIR}/.venv/bin/activate"
fi

echo "----> Coffea environment ready"
