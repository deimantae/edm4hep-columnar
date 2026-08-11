'''
Run configurable EDM4hep file reduction, conversion to RNTuple, histogramming 
and validation commands.
'''

import sys
from argparse import ArgumentParser

import awkward as ak
import hist
import uproot
import yaml

from coffea import util
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
        schemaclass=FCC.get_schema(version="pre-edm4hep1"),
        mode="eager",
        iteritems_options={"filter_name": "/^(?!.*(PARAMETERS|_.*Map))/"},
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
    # Create Coffea histogram objects from the filtered dictionary of arrays
    histograms = {}

    for variable_name, values in variables.items():
        values = ak.ravel(values)

        # Skip empty variables
        if len(values) == 0:
            continue
        
        minimum = float(ak.min(values))
        maximum = float(ak.max(values))

        # Avoid a zero width range
        if minimum == maximum:
            margin = 0.5 if minimum == 0 else 0.1 * abs(minimum)
            minimum -= margin
            maximum += margin

        histogram = (
            hist.Hist.new
            .Reg(100, minimum, maximum)
            .Double()
            .fill(values)
        )

        histograms[variable_name] = histogram

    return histograms

def histogram_edm4hep(args):
    # Create histograms directly from the original EDM4hep file
    selected_variables = configure_analysis(
        args.input_file,
        args.parameters_file
        )
    
    histograms = create_histograms(selected_variables)
    
    util.save(histograms, args.output_file)
    print(f"Saved histogram objects to {args.output_file}")
    #look at coffea util
    # best if root files
    
    
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


def histogram_rntuple(args):
    # Open the reduced RNTuple
    with uproot.open(args.input_file) as input_file:
        arrays = input_file["Events"].arrays()
    
    # Convert the Awkward array to a dictionary
    variables = {}

    for variable_name in arrays.fields:
        variables[variable_name] = arrays[variable_name]

    histograms = create_histograms(variables)

    util.save(histograms, args.output_file)
    print(f"Saved histogram objects to {args.output_file}")


def compare(args):
    # Compare two Coffea histogram files.
    compare_histograms(args.histograms_1, args.histograms_2, args.output_file)

    
def build_parser():
    # Create the command-line parser and subcommands
    parser = ArgumentParser(description="Run a configurable EDM4hep analysis.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Read an EDM4hep file, apply the configured analysis steps "
        "and write the selected variables to an reduced RNTuple"
    )
    convert_parser.add_argument("--parameters-file", required=True, type=str,
                        help="YAML file containing the analysis configuration.")
    convert_parser.add_argument("--input-file", required=True, type=str,
                        help="Input EDM4hep ROOT file.")
    convert_parser.add_argument("--output-file", default="output.root", type=str,
                        help="Output RNTuple ROOT file.")
    convert_parser.set_defaults(function=convert)
    
    # EDM4hep histogram command
    edm4hep_parser = subparsers.add_parser(
        "histogram-edm4hep",
        help="Read an EDM4hep file, apply the configured analysis steps "
        "and save Coffea histogram objects to a .coffea file."
    )
    edm4hep_parser.add_argument("--parameters-file", required=True, type=str,
                        help="YAML file containing the analysis configuration.")
    edm4hep_parser.add_argument("--input-file", required=True, type=str,
                        help="Input EDM4hep ROOT file.")
    edm4hep_parser.add_argument("--output-file", required=True, type=str,
                                help="Output Coffea histogram file.")
    edm4hep_parser.set_defaults(function=histogram_edm4hep)
    
    # RNTuple histogram command
    rntuple_parser = subparsers.add_parser(
        "histogram-rntuple",
        help="Read an RNTuple ROOT file and save Coffea histogram objects.")
    rntuple_parser.add_argument("--input-file", required=True, type=str,
                        help="Input RNTuple ROOT file.")
    rntuple_parser.add_argument("--output-file", required=True, type=str,
                                help="Output Coffea histogram file.")
    rntuple_parser.set_defaults(function=histogram_rntuple)
    
    # Comparison command
    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare two Coffea histogram files",
    )
    compare_parser.add_argument("histograms_1", help="First histogram file.")
    compare_parser.add_argument("histograms_2", help="Second histogram file.")
    compare_parser.add_argument("--output-file",
                                default="histogram_comparison.pdf",
                                help="Output PDF file.")
    compare_parser.set_defaults(function=compare)

    return parser


parser = build_parser()
args = parser.parse_args()
args.function(args)