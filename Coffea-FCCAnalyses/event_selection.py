import awkward as ak
import numpy as np

"""
Modify this function to select events.
Return a boolean Awkward array with one value per event.
"""

def select_events(events):
    # Example: keep events with at least one jet with pt > 90 GeV
    jet_pt = np.sqrt(events.Jet.px*events.Jet.px + 
                     events.Jet.py*events.Jet.py)
    return ak.any(jet_pt > 90, axis=1)