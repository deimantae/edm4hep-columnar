"""
Benchmark one EDM4hep analysis workflow.

Imports and argument parsing are excluded from the time measurement.
Input loading, processing and output writing are included.
"""

import argparse
import importlib
import io
import os
import statistics
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path


DIR = Path(__file__).resolve().parent

WORKFLOWS = {
    "fccanalyses": DIR / "FCC-Analyses",
    "coffea": DIR / "Coffea-FCCAnalyses"
}


# Run one workflow command and measure its execution time
def time_command(function, arguments):    
    start = time.perf_counter_ns()
    
    # Hide output of the commands
    with redirect_stdout(io.StringIO()):
        function(arguments)
        
    elapsed = time.perf_counter_ns() - start
    
    return elapsed / 1e9 # convert ns to s


# Run all three benchmarked commands once
def run_workflow(workflow, workflow_dir, input_file, output_dir):
    parameters = workflow_dir / "parameters.yaml"

    # Temporary output files used by the workflow
    reduced_file = output_dir / "reduced.root"
    edm4hep_histograms = output_dir / "histograms_edm4hep.root"
    rntuple_histograms = output_dir / "histograms_rntuple.root"

    # Pass arguments to each function
    edm4hep_time = time_command(
        workflow.histogram_edm4hep,
        argparse.Namespace(
            input_file=str(input_file),
            output_file=str(edm4hep_histograms),
            parameters_file=str(parameters)
        )
    )

    conversion_time = time_command(
        workflow.convert,
        argparse.Namespace(
            input_file=str(input_file),
            output_file=str(reduced_file),
            parameters_file=str(parameters)
        )
    )

    rntuple_time = time_command(
        workflow.histogram_rntuple,
        argparse.Namespace(
            input_file=str(reduced_file),
            output_file=str(rntuple_histograms)
        )
    )

    # Keep the individual timings and the total reduced workflow time
    return {
        "histogram-edm4hep": edm4hep_time,
        "conversion": conversion_time,
        "histogram-rntuple": rntuple_time,
        "total": conversion_time + rntuple_time
    }


# Format repeated measurements
def format_time(values):
    mean = statistics.mean(values)
    sigma = statistics.stdev(values)

    return f"{mean:.3f} ± {sigma:.3f} s"


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark an EDM4hep analysis workflow"
    )

    # Select which implementation to benchmark
    parser.add_argument("workflow", choices=WORKFLOWS)
    # Original EDM4hep input file
    parser.add_argument("input_file", type=Path)
    # Number of measured runs after the warm-up
    parser.add_argument("--runs", type=int, default=5, help="Number of runs")
    args = parser.parse_args()

    # At least two measurements required for std
    if args.runs < 2:
        parser.error("--runs must be at least 2")

    input_file = args.input_file.resolve()

    if not input_file.is_file():
        parser.error(f"Input file does not exist: {input_file}")

    workflow_dir = WORKFLOWS[args.workflow]
    os.chdir(workflow_dir) # run everything from the workflow dir

    # Import the selected workflow before timing starts
    sys.path.insert(0, str(workflow_dir))
    workflow = importlib.import_module("edm4hep_columnar")

    # Store all measured times
    results = {
        "histogram-edm4hep": [],
        "conversion": [],
        "histogram-rntuple": [],
        "total": []
    }

    # Create a temporary directory for reduced files and histograms
    # Deleted when the benchmark finishes
    with tempfile.TemporaryDirectory(
        prefix="edm4hep-benchmark-",
        dir=DIR
    ) as temporary_directory:

        output_dir = Path(temporary_directory)

        # First run warms the caches and is not included in the statistics
        print("Warm-up")
        run_workflow(workflow, workflow_dir, input_file, output_dir)

        # Perform the measured runs
        for run in range(args.runs):
            print(f"Run {run + 1}/{args.runs}")

            times = run_workflow(workflow, workflow_dir, input_file, output_dir)

            # Add timings to result lists
            for name in results:
                results[name].append(times[name])

    # Print statistics
    if args.workflow == "fccanalyses":
        workflow_name = "FCCAnalyses"
    else:
        workflow_name = "Coffea"
    
    print(
        f"\n{workflow_name} benchmark results\n"
        f"(mean ± sigma, {args.runs} measured runs)\n"
    )
    
    print("EDM4hep")
    print(
        "  histogramming:            "
        f"{format_time(results['histogram-edm4hep'])}"
    )
    
    print("\nReduced RNTuple")
    print(
        "  conversion:               "
        f"{format_time(results['conversion'])}"
    )
    print(
        "  histogramming:            "
        f"{format_time(results['histogram-rntuple'])}"
    )
    print(
        "  total:                    "
        f"{format_time(results['total'])}"
    )

main()