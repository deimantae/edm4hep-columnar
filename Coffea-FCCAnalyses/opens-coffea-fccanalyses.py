import awkward as ak
import uproot
import yaml
import hist
import sys

from coffea.nanoevents import FCC, NanoEventsFactory
from argparse import ArgumentParser
from coffea import util

from analysis_helpers import add_fields, apply_selection, collect_variables

# Example FCC winter 2023 sample
'''
fname = (
    "root://eospublic.cern.ch//eos/experiment/fcc/ee/generation/"
    "DelphesEvents/winter2023/IDEA/wzp6_ee_mumuH_Hbb_ecm240/"
    "events_159112833.root"
)
'''

fname = "events_159112833.root"

parser = ArgumentParser(description="Additional analysis arguments")
parser.add_argument("--parameters-file", required=True, type=str,
                    help="YAML file containing the variables.")
args = parser.parse_args()


# Store YAML contents as a dictionary
with open(args.parameters_file, "r") as file:
    contents = yaml.safe_load(file) or {}
    
selection = contents.get("selection") # optional event selection
additional_fields = contents.get("additional_fields") or [] # optional fields
variables = contents.get("variables") or {} # variables to histogram

# Open the file
events = NanoEventsFactory.from_root(
    {fname: "events"},
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
with uproot.recreate("output.root") as output_file:
    output_file.mkrntuple("Events", output_array)
    
print("Saved output RNTuple to output.root")