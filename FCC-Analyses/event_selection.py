"""
Example event selection functions for FCCAnalyses.

Each function takes an RDataFrame as input and returns the filtered
RDataFrame. Reference the function in the YAML configuration.
"""

def select_pt(dframe):
    # Example: keep events with at least one jet with pT > 90 GeV
    return dframe.Filter(
        "ROOT::VecOps::Any(ROOT::VecOps::sqrt("
        "Jet.momentum.x*Jet.momentum.x + "
        "Jet.momentum.y*Jet.momentum.y) > 90)"
    )

def select_particle_mass(dframe):
    # Example: keep events with at least one reconstructed particle
    # with mass between 120 and 130 GeV
    return dframe.Filter(
        "ROOT::VecOps::Any((ReconstructedParticles.mass > 120) && "
        "(ReconstructedParticles.mass < 130))"
    )