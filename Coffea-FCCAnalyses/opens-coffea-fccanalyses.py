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

# Open the EDM4hep file
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
    selected_variables = collect_variables(events, variables)

except (ValueError, TypeError, KeyError, AttributeError) as error:
    print(f"Configuration error: {error}")
    sys.exit(1)

# Create histograms from the filtered EDM4hep file
edm4hep_histograms = {}

for variable_name, values in selected_variables.items():
    edm4hep_histograms[variable_name] = (
        hist.Hist.new
        .Reg(50, 0, 150)
        .Double()
        .fill(ak.ravel(values))
    )
    
util.save(edm4hep_histograms, "edm4hep_histograms.coffea")
print("Saved EDM4hep histogram objects to edm4hep_histograms.coffea")
    
# Write filtered variables to RNTuple
rntuple_array = ak.zip(selected_variables, depth_limit=1)

with uproot.recreate(args.output_file) as output_file:
    output_file.mkrntuple("Events", rntuple_array)
    
print(f"Saved RNTuple to {args.output_file}")   

# Open the RNTuple file
with uproot.open(args.output_file) as input_file:
    rntuple_events = input_file["Events"].arrays()

# Create RNTuple histogram objects
rntuple_histograms = {}

for variable_name in rntuple_events.fields:
    rntuple_histograms[variable_name] = (
        hist.Hist.new
        .Reg(50, 0, 150)
        .Double()
        .fill(ak.ravel(rntuple_events[variable_name]))
    )

util.save(rntuple_histograms, "rntuple_histograms.coffea")
print("Saved RNTuple histogram objects to rntuple_histograms.coffea")