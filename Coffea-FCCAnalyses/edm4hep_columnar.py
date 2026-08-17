'''
Run configurable EDM4hep file reduction, conversion to RNTuple, histogramming 
and validation commands.
'''

import sys
from argparse import ArgumentParser

import awkward as ak
import ROOT
import uproot
import yaml

from coffea.nanoevents import FCC, NanoEventsFactory

from analysis_helpers import add_fields, apply_selection, collect_variables
from comparison import compare_histograms


def load_configuration(parameters_file):
    # Load the analysis configuration from a YAML file
    # and store its contents as a dictionary
    with open(parameters_file, "r") as file:
        contents = yaml.safe_load(file) or {}

    # Optional event selection
    selection = contents.get("selection")

    # Optional additional fields
    additional_fields = contents.get("additional_fields") or []

    # Variables to collect
    variables = contents.get("variables") or {}

    return selection, additional_fields, variables


def open_edm4hep(input_file):
    # Open the EDM4hep ROOT file
    return NanoEventsFactory.from_root(
        {input_file: "events"},
        schemaclass=FCC.get_schema(version="edm4hep1"),
        mode="eager",
    #    iteritems_options={"filter_name": "/^(?!.*(PARAMETERS|_.*Map))/"},
        iteritems_options={"filter_name": "/^(?!.*(PARAMETERS|_.*Map|RecoMCLink)).*$/"},
        entry_stop=100,
    ).events()


def configure_analysis(input_file, parameters_file):
    # Load and apply optional additional fields and/or event selection
    selection, additional_fields, variables = (
        load_configuration(parameters_file)
        )

    events = open_edm4hep(input_file)

    try:
        # Add user-defined fields to the events array
        events = add_fields(events, additional_fields)

        # Apply the event selection
        events = apply_selection(events, selection)

    except (ValueError, TypeError, KeyError) as error:
        print(f"Configuration error: {error}")
        sys.exit(1)

    try:
        # Collect all indicated variables
        selected_variables = collect_variables(events, variables)

    except (ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"Configuration error: {error}")
        sys.exit(1)

    return selected_variables


def create_histograms(variables):
    # Create ROOT histogram objects from the filtered dictionary of arrays
    histograms = {}

    # Flatten Awkward arrays first
    for variable_name, values in variables.items():
        values = ak.ravel(values)
        # Skip empty variables
        if len(values) == 0:
            continue

        values = ak.to_numpy(values)
        histogram = ROOT.TH1D(variable_name, "", 100, 0, 0)

        for value in values:
            histogram.Fill(value)
        histograms[variable_name] = histogram

    return histograms


def write_histograms(histograms, output_file):
    # Write ROOT histogram objects
    root_file = ROOT.TFile(output_file, "RECREATE")

    for histogram in histograms.values():
        histogram.Write()
    root_file.Close()

    print(f"Saved histogram objects to {output_file}")


# Commands

def convert(args):
    # Write filtered variables to a reduced RNTuple
    selected_variables = configure_analysis(
        args.input_file,
        args.parameters_file
        )

    rntuple_array = ak.zip(selected_variables, depth_limit=1)

    with uproot.recreate(args.output_file) as output_file:
        output_file.mkrntuple("Events", rntuple_array)

    print(f"Saved RNTuple to {args.output_file}")


def histogram_edm4hep(args):
    # Create histograms directly from the original EDM4hep file
    selected_variables = configure_analysis(
        args.input_file,
        args.parameters_file
    )

    histograms = create_histograms(selected_variables)
    write_histograms(histograms, args.output_file)


def histogram_rntuple(args):
    # Open the reduced RNTuple
    with uproot.open(args.input_file) as input_file:
        arrays = input_file["Events"].arrays()

    # Convert the Awkward array to a dictionary
    variables = {}

    for variable_name in arrays.fields:
        variables[variable_name] = arrays[variable_name]

    histograms = create_histograms(variables)
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


parser = build_parser()
args = parser.parse_args()
args.function(args)
