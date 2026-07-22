import uproot
import awkward as ak

f1 = uproot.open("jets_RDF.root")
f2 = uproot.open("jets_coffea.root")

# File type
print("RDataFrame: ", f1["Events"].classname)
print("Coffea: ", f2["Events"].classname)

# Branches
#print(f1["Events"].keys())
#print(f2["Events"].keys())
print("Same keys:", set(f1["Events"].keys()) == set(f2["Events"].keys()))
print("Same number", (f1["Events"].num_entries)==(f2["Events"].num_entries))

# Compare data
for branch in f1["Events"].keys():
    same = ak.almost_equal(
        f1["Events"][branch].array(),
        f2["Events"][branch].array()
    ) # Checks if two awkward arrays are the same
    print(branch, same)
