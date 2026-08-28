"""
Example event selection functions for FCCAnalyses.

Each function takes an RDataFrame as input and returns the filtered
RDataFrame. Reference the function in the YAML configuration.
"""


def select_jets(dframe):
    # Keep events with at least two jets with energy > 10 GeV
    return dframe.Filter(
        "ROOT::VecOps::Sum(ReconstructedParticle::getE(Jet) > 10) >= 2"
    )


def select_visible_energy(dframe):
    # Keep events with total reconstructed energy > 50 GeV
    return dframe.Filter(
        "ROOT::VecOps::Sum("
        "ReconstructedParticle::getE(ReconstructedParticles)"
        ") > 50"
    )