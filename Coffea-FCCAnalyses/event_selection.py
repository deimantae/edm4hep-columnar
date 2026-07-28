import awkward as ak
import numpy as np

"""
Example event selection functions.

Each function takes the Coffea events object as input and returns
a boolean Awkward array with one value per event. Reference the
function in the YAML configuration.
"""

def select_pt(events):
    # Example: keep events with at least one jet with pT > 90 GeV
    jet_pt = np.sqrt(
        events.Jet.px * events.Jet.px +
        events.Jet.py * events.Jet.py
    )
    return ak.any(jet_pt > 90, axis=1)


def select_particle_mass(events):
    # Example: keep events with at least one reconstructed particle
    # with mass between 120 and 130 GeV
    return ak.any(
        (events.ReconstructedParticles.mass > 120) &
        (events.ReconstructedParticles.mass < 130),
        axis=1,
    )