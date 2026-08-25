#!/bin/bash

# Script must be sourced so environment changes are kept in the current shell
if [ "${0}" == "${BASH_SOURCE[0]}" ]; then
    echo "ERROR: Set up the environment with:"
    echo "  source setup.sh"
    exit 1
fi

# Find directory containing this script
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)


# Load ROOT, EDM4hep, podio and FCCAnalyses dependencies from Key4hep
echo "----> Setting up Key4hep environment..."
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh

# Hide ROOT RDataFrame Snapshot information messages.
export ROOT_RDF_SNAPSHOT_INFO=0

# Directory for additional Python packages
PACKAGE_DIR="${SCRIPT_DIR}/.python-packages"

# Install additional Python dependencies if needed
if [ ! -d "${PACKAGE_DIR}" ]; then
    echo "----> Installing Python dependencies..."
    mkdir -p "${PACKAGE_DIR}"

    python -m pip install -q \
        --target "${PACKAGE_DIR}" \
        -r "${SCRIPT_DIR}/requirements.txt"
fi

# Make the locally installed packages available to Python
export PYTHONPATH="${PACKAGE_DIR}:${PYTHONPATH:-}"

echo "----> FCCAnalyses environment ready"
