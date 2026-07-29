"""
Example functions for creating new particle collections.
"""

def particle_collections(events):
    muons = events.ReconstructedParticles[events.Muonidx0.index]
    electrons = events.ReconstructedParticles[events.Electronidx0.index]
    photons = events.ReconstructedParticles[events.Photonidx0.index]

    return {
        "Muon": muons,
        "Electron": electrons,
        "Photon": photons,
    }