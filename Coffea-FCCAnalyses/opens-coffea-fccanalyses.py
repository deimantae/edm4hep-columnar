import sys
from argparse import ArgumentParser

import awkward as ak
import hist
import uproot
import yaml

from coffea import util
from coffea.nanoevents import FCC, NanoEventsFactory

from analysis_helpers import add_fields, apply_selection, collect_variables

# Command-line arguments
parser = ArgumentParser(description="Run a configurable EDM4hep analysis.")
parser.add_argument("--parameters-file", required=True, type=str,
                    help="YAML file containing the analysis configuration.")
parser.add_argument("--input-file", required=True, type=str,
                    help="Input EDM4hep ROOT file path.")
parser.add_argument("--output-file", default="output.root", type=str,
                    help="Output RNTuple file path.")

args = parser.parse_args()

# Store YAML contents as a dictionary
with open(args.parameters_file, "r") as file:
    contents = yaml.safe_load(file) or {}

# Optional event selection
selection = contents.get("selection")

# Optional additional fields
additional_fields = contents.get("additional_fields") or []

# Variables to histogram
variables = contents.get("variables") or {}

# Open the file
events = NanoEventsFactory.from_root(
    {args.input_file: "events"},
    schemaclass=FCC.get_schema(version="pre-edm4hep1"),
    mode="eager",
    iteritems_options={"filter_name": "/^(?!.*(PARAMETERS|_.*Map))/"},
    entry_stop=100,
).events()

# Apply optional additional fields and/or event selection
try:
    # Add user-defined fields to the events array
    events = add_fields(events, additional_fields)

    # Apply the event selection
    events = apply_selection(events, selection)

except (ValueError, TypeError, KeyError) as error:
    print(f"Configuration error: {error}")
    sys.exit(1)

# Collect all indicated variables
try:
    variables_output = collect_variables(events, variables)

except (ValueError, TypeError, KeyError, AttributeError) as error:
    print(f"Configuration error: {error}")
    sys.exit(1)

# Create histogram objects
histograms = {}

for output_name, values in variables_output.items():
    histogram = (
        hist.Hist.new
        .Reg(50, 0, 150)
        .Double()
        .fill(ak.ravel(values))
    )

    histograms[output_name] = histogram

# Combine all calculated variables into one output array
output_array = ak.zip(variables_output, depth_limit=1)
util.save(histograms, "input_histograms.coffea")
print("Saved input histogram objects to input_histograms.coffea")

# Create RNTuple output file
with uproot.recreate(args.output_file) as output_file:
    output_file.mkrntuple("Events", output_array)
    
print(f"Saved output RNTuple to {args.output_file}")