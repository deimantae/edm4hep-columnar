"""
Example event selection functions for FCCAnalyses.

Each function takes an RDataFrame as input and returns the filtered
RDataFrame. Reference the function in the YAML configuration.
"""


def select_pt(dframe):
    # Example: keep events with at least one jet with pT > 90 GeV
    return dframe.Filter(
        "ROOT::VecOps::Any(ReconstructedParticle::getPt(Jet) > 90)"
    )


def select_particle_mass(dframe):
    # Example: keep events with at least one reconstructed particle
    # with mass between 120 and 130 GeV
    return dframe.Filter(
        "ROOT::VecOps::Any("
        "(ReconstructedParticle::getMass(ReconstructedParticles) > 120) && "
        "(ReconstructedParticle::getMass(ReconstructedParticles) < 130)"
        ")"
    )
