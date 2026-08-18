'''
Run configurable EDM4hep file reduction, conversion to RNTuple, histogramming 
and validation commands.
'''
import sys
import yaml
from argparse import ArgumentParser
from pathlib import Path

import ROOT

from analysis_helpers import add_fields, apply_selection, collect_variables
from comparison import compare_histograms

# Load FCCAnalyses
# Adapted from FCCAnalyses/examples/data_source/standalone.py

ROOT.gSystem.Load("libFCCAnalyses")
ROOT.gInterpreter.Declare("""
#include "edm4hep/EventHeaderCollection.h"
#include "edm4hep/TrackCollection.h"
""")

if ROOT.dummyLoader:
    print("----> DEBUG: Found FCCAnalyses library.")
    ROOT.gInterpreter.Declare("using namespace FCCAnalyses::PodioSource;")

functions_header = Path(__file__).resolve().parent / "functions.h"
ROOT.gInterpreter.Declare(f'#include "{functions_header}"')

print("----> INFO: Loading analyzers from libFCCAnalyses...")

# Load podio DataSource
if ROOT.podio.DataSource:
    print("----> DEBUG: Found Podio ROOT DataSource.")


def load_configuration(parameters_file):
    # Load the analysis configuration from a YAML file
    # and store its contents as a dictionary
    with open(parameters_file, "r") as file:
        contents = yaml.safe_load(file) or {}

    # Optional event selection
    selection = contents.get("selection")

    # Optional additional fields
    additional_fields = contents.get("additional_fields") or {}

    # Variables to collect
    variables = contents.get("variables") or {}

    return selection, additional_fields, variables


def open_edm4hep(input_file):
    # Open the EDM4hep ROOT file using podio::DataSource
    input_list = [input_file]

    print("----> INFO: Loading events through podio::DataSource...")

    try:
        dframe = ROOT.podio.CreateDataFrame(input_list)
    except TypeError as excp:
        print("----> ERROR: Unable to build dataframe!")
        print(excp)
        raise

    # TODO: Remove temporary event limit after debugging
    return dframe.Range(100)


def configure_analysis(input_file, parameters_file):
    # Load and apply optional additional fields and/or event selection
    selection, additional_fields, variables = (
        load_configuration(parameters_file)
    )

    dframe = open_edm4hep(input_file)

    try:
        # Add user-defined fields to the dataframe
        dframe = add_fields(dframe, additional_fields)
        
        # Apply the event selection
        dframe = apply_selection(dframe, selection)

    except (ValueError, TypeError, KeyError) as error:
        print(f"Configuration error: {error}")
        sys.exit(1)

    try:
        # Collect all indicated variables
        dframe, branches = collect_variables(dframe, variables)

    except (ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"Configuration error: {error}")
        sys.exit(1)

    return dframe, branches


def create_histograms(dframe, branches):
    # Create ROOT histogram objects
    histograms = []
    
    for branch_name in branches:
        branch_name = str(branch_name)

        histogram = dframe.Histo1D(
            (branch_name, "", 100, 0, 0),
            branch_name,
        )
        histograms.append(histogram)

    return histograms


def write_histograms(histograms, output_file):
    # Write ROOT histogram objects
    root_file = ROOT.TFile(output_file, "RECREATE")

    for histogram in histograms:
        # Skip empty variables
        if histogram.GetEntries() == 0:
            continue
        histogram.Write()

    root_file.Close()

    print(f"Saved histogram objects to {output_file}")


# Commands

def convert(args):
    # Configure the EDM4hep analysis
    dframe, branches = configure_analysis(
        args.input_file,
        args.parameters_file
    )

    # Configure Snapshot to write an RNTuple
    snapshot_options = ROOT.RDF.RSnapshotOptions()

    snapshot_options.fOutputFormat = (
        ROOT.RDF.ESnapshotOutputFormat.kRNTuple
    )

    # Write reduced RNTuple
    dframe.Snapshot(
        "events",
        args.output_file,
        branches,
        snapshot_options,
    )

    print(f"Saved reduced RNTuple to {args.output_file}")


def histogram_edm4hep(args):
    # Create histograms directly from the EDM4hep file
    dframe, branches = configure_analysis(
        args.input_file,
        args.parameters_file
    )
    
    histograms = create_histograms(dframe, branches)
    write_histograms(histograms, args.output_file)


def histogram_rntuple(args):
    # Create histograms from the reduced RNTuple
    dframe = ROOT.RDataFrame("events", args.input_file)
    branches = dframe.GetColumnNames()
    
    histograms = create_histograms(dframe, branches)
    write_histograms(histograms, args.output_file)


def compare(args):
    # Compare two ROOT histogram files
    compare_histograms(args.histograms_1, args.histograms_2, args.output_file)


def build_parser():
    # Create the command-line parser and subcommands
    parser = ArgumentParser(description="Run a configurable EDM4hep analysis.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert EDM4hep to a reduced RNTuple"
    )
    convert_parser.add_argument("--parameters-file", required=True, type=str,
                        help="Analysis configuration file")
    convert_parser.add_argument("--input-file", required=True, type=str,
                        help="Input EDM4hep ROOT file")
    convert_parser.add_argument("--output-file", default="output.root", type=str,
                        help="Output reduced RNTuple file")
    convert_parser.set_defaults(function=convert)

    # EDM4hep histogram command
    edm4hep_parser = subparsers.add_parser(
        "histogram-edm4hep",
        help="Create histograms from the original EDM4hep file"
    )
    edm4hep_parser.add_argument("--parameters-file", required=True, type=str,
                                help="Analysis configuration file")
    edm4hep_parser.add_argument("--input-file", required=True, type=str,
                                help="Input EDM4hep file")
    edm4hep_parser.add_argument("--output-file", required=True, type=str,
                                help="Output histogram file")
    edm4hep_parser.set_defaults(function=histogram_edm4hep)
    
    # RNTuple histogram command
    rntuple_parser = subparsers.add_parser(
        "histogram-rntuple",
        help="Create histograms from the reduced RNTuple file"
        )
    rntuple_parser.add_argument("--input-file", required=True, type=str,
                                help="Input reduced RNTuple file")
    rntuple_parser.add_argument("--output-file", required=True, type=str,
                                help="Output histogram file")
    rntuple_parser.set_defaults(function=histogram_rntuple)
    
    # Comparison command
    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare histograms and verify the conversion",
    )
    compare_parser.add_argument("histograms_1", help="First histogram file")
    compare_parser.add_argument("histograms_2", help="Second histogram file")
    compare_parser.add_argument("--output-file",
                                default="histogram_comparison.pdf",
                                help="Output PDF file")
    compare_parser.set_defaults(function=compare)

    return parser


# Run the CLI only when the script is executed directly
def main():
    parser = build_parser()
    args = parser.parse_args()
    args.function(args)


# Allow the functions to be imported without running the CLI
if __name__ == "__main__":
    main()