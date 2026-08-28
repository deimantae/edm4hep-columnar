"""
Example event selection functions.

Each function takes the Coffea events object as input and returns
a boolean Awkward array with one value per event. Reference the
function in the YAML configuration.
"""

import awkward as ak

def select_jets(events):
    # Keep events with at least two jets with energy > 10 GeV
    good_jets = events.Jet.energy > 10

    return ak.sum(good_jets, axis=1) >= 2


def select_visible_energy(events):
    # Keep events with total reconstructed energy > 50 GeV
    visible_energy = ak.sum(events.ReconstructedParticles.energy, axis=1)

    return visible_energy > 50
