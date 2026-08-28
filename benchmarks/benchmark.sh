#!/bin/bash

set -e  # stop after first error

# Find repository directory
REPO_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Check command-line arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input.root>"
    exit 1
fi

INPUT_FILE="$1"

# Create a unique temporary directory for this batch job
JOB_ID="${BENCHMARK_JOB_ID:-local-$$}"
JOB_TMPDIR="${_CONDOR_SCRATCH_DIR:-/tmp}/edm4hep-benchmark-${JOB_ID}"
mkdir -p "$JOB_TMPDIR"
export TMPDIR="$JOB_TMPDIR"

# Print CPU model
echo "CPU: $(lscpu | awk -F: '/Model name/{gsub(/^[ \t]+/, "", $2); print $2; exit}')"

# Run FCCAnalyses benchmark
echo "Running FCCAnalyses benchmark"

(
    set --  # clean positional arguments
    source "${REPO_DIR}/FCC-Analyses/setup.sh"
    python -u "${REPO_DIR}/benchmark.py" fccanalyses "$INPUT_FILE"
)

# Run Coffea benchmark
echo
echo "Running Coffea benchmark"

(
    set --  # clean positional arguments
    source "${REPO_DIR}/Coffea-FCCAnalyses/setup.sh"
    python -u "${REPO_DIR}/benchmark.py" coffea "$INPUT_FILE"
)

echo
echo "Done!"
