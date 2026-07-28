import numpy as np
import awkward as ak
import uproot
import yaml
import hist
import importlib.util
from coffea.nanoevents import FCC, NanoEventsFactory
from argparse import ArgumentParser
from coffea import util

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
    contents = yaml.safe_load(file)
    
selection = contents.get("selection")
variables = contents.get("variables", {})

# Open the file
events = NanoEventsFactory.from_root(
    {fname: "events"},
    schemaclass=FCC.get_schema(version="pre-edm4hep1"),
    mode="eager",
    iteritems_options={"filter_name": "/^(?!.*(PARAMETERS|_.*Map))/"},
    entry_stop=100,
).events()

# Create Muon, Electron and Photon collections from ReconstructedParticles
muons = events.ReconstructedParticles[events.Muonidx0.index]
electrons = events.ReconstructedParticles[events.Electronidx0.index]
photons = events.ReconstructedParticles[events.Photonidx0.index]

events = ak.with_field(events, muons, "Muon")
events = ak.with_field(events, electrons, "Electron")
events = ak.with_field(events, photons, "Photon")

# Apply the event selection
if selection is not None:
    has_file = "file" in selection
    has_function = "function" in selection
    has_filter = "filter" in selection

    # File and function must always be specified together
    if has_file != has_function:
        raise ValueError(
            "'file' and 'function' must be specified together."
        )

    # Only one selection method may be used
    if has_file and has_filter:
        raise ValueError(
            "Selection must use either 'file' + 'function' "
            "or 'filter', not both."
        )

    if not has_file and not has_filter:
        raise ValueError(
            "Selection must contain either 'file' + 'function' "
            "or 'filter'."
        )

    # Use Python selection function
    if has_file:
        spec = importlib.util.spec_from_file_location(
            "selection",
            selection["file"],
        )

        selection_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(selection_module)

        selection_function = getattr(
            selection_module,
            selection["function"],
        )

        mask = selection_function(events)

    # Use an inline Python filter expression
    else:
        filter_namespace = {
            "ak": ak,
            "np": np,
        }

        for collection_name in events.fields:
            filter_namespace[collection_name] = getattr(
                events,
                collection_name,
            )

        mask = eval(
            selection["filter"],
            filter_namespace,
        )

    print("Selected events:", ak.sum(mask))
    print("Rejected events:", ak.sum(~mask))

    events = events[mask]

# Collect all indicated variables
variables_output = {}
histograms = {}

for collection_name, variable_list in variables.items():
    if variable_list is None:
        continue # for empty entries

    collection = getattr(events, collection_name)

    for variable in variable_list:
        
        # String variable
        if isinstance(variable, str):
            variable_name = variable
            values = getattr(collection, variable_name)
            
        # Mathematical operation variable
        elif isinstance(variable, dict):
            if len(variable) != 1:
                raise ValueError(
                    "Variable definition must contain only "
                    f"one expression: {variable!r}"
                )
            
            for variable_name, expression in variable.items():
                for field in collection.fields:
                    expression = expression.replace(
                        field, f"collection.{field}"
                        )
                values = eval(expression)
                
        # If parameters file format is wrong
        else:
            raise TypeError(
                f"Unsupported variable definition: {variable!r}"
                )

        output_name = f"{collection_name}_{variable_name}"
        variables_output[output_name] = values
        
        # Create histogram objects
        histogram = (
            hist.Hist.new
            .Reg(50, 0, 150)
            .Double()
            .fill(ak.ravel(values))
            )
        
        histograms[output_name] = histogram

output_array = ak.zip(variables_output, depth_limit=1)
util.save(histograms, "input_histograms.coffea")
print("Saved input histogram objects to input_histograms.coffea")

# Create RNTuple output file 
with uproot.recreate("output.root") as output_file:
    output_file.mkrntuple("Events", output_array)
    
print("Saved output RNTuple to output.root")