import awkward as ak
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema
import uproot

# Example file from the Coffea tests
fname = "nano_dy.root"

# OpenCMS data file
#fname = "root://eospublic.cern.ch//eos/opendata/cms/Run2016H/DoubleMuon/NANOAOD/UL2016_MiniAODv2_NanoAODv9-v1/2510000/127C2975-1B1C-A046-AABF-62B77E757A86.root"

# Open a CMS NanoAOD file
NanoAODSchema.error_missing_event_ids = False #this was included in the examples
events = NanoEventsFactory.from_root(
    {fname: "Events"}, #Open tree inside file
    schemaclass=NanoAODSchema, #Interpret as CMS NanoAOD
    entry_stop=1000
).events()

# Collect all jet properties
jets = events.Jet
#print(jets.fields)

# Create a new file
jet_output = {
    "nJet": ak.num(jets)
}
for field in jets.fields:
    if not field.endswith("G"):
        jet_output[f"Jet_{field}"] = jets[field]

"""
#--------------TTree version--------------
with uproot.recreate("jets_coffea.root") as output_file:
    output_file.mktree("Events", jet_output)

#Check
with uproot.open("jets_coffea.root") as file:
    tree = file["Events"]
    print(tree.keys())

"""

#--------------RNTuple version--------------
with uproot.recreate("jets_coffea.root") as output_file:
    output_file.mkrntuple("Events", jet_output)

# Check
fname2 = "jets_coffea.root"

NanoAODSchema.error_missing_event_ids = False
events2 = NanoEventsFactory.from_root(
    {fname2: "Events"}, #Open tree inside file
    schemaclass=NanoAODSchema #Interpret as CMS NanoAOD
).events()

jets2 = events2.Jet
print(jets2.fields)
