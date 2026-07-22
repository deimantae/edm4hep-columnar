import ROOT

# Open a CMS NanoAOD file
df = ROOT.RDataFrame("Events", "nano_dy.root")

# Collect all jet properties
jet_prop = ["nJet"]
for col in df.GetColumnNames():
    col = str(col) #Converting C++ std::str to Python str 
    if col.startswith("Jet_"): jet_prop.append(col)

# Create a new file
df.Snapshot("Events", "jets_RDF.root", jet_prop)

# Check
df2 = ROOT.RDataFrame("Events", "jets_RDF.root")
for col in df2.GetColumnNames():
    print(col)
