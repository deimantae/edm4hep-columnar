"""
Example functions for creating new particle collections.
"""

import awkward as ak
import numpy as np

# ---------- Helper functions ----------


def p(particles):
    # Return the magnitude of the momentum
    return np.sqrt(particles.px**2 + particles.py**2 + particles.pz**2)


def pt(particles):
    # Return the transverse momentum
    return np.sqrt(particles.px**2 + particles.py**2)


def phi(particles):
    # Return the azimuthal angle
    return np.arctan2(particles.py, particles.px)


def eta(particles):
    # Return the pseudorapidity
    particle_pt = pt(particles)

    return np.arcsinh(
        particles.pz / ak.where(particle_pt != 0, particle_pt, np.nan)
    )


# Return the track state associated with reco particles
def track_information(particles):

    # Match each reco particle to its track
    tracks = particles.get_tracks

    # Match each track to its corresponding track state
    tracks = ak.firsts(tracks, axis=2)
    states = ak.firsts(tracks.trackStates, axis=2)

    return states


def calculate_muon_isolation(muons, events, dr_min=0.01, dr_max=0.5):
    particles = events.ReconstructedParticles

    # Add a new axis to compare every muon with every reconstructed particle
    muon_eta = eta(muons)[:, :, None]
    muon_phi = phi(muons)[:, :, None]
    muon_p = p(muons)

    particle_eta = eta(particles)[:, None, :]
    particle_phi = phi(particles)[:, None, :]
    particle_p = p(particles)[:, None, :]

    # Compute the angular distance between each muon and particle
    delta_eta = muon_eta - particle_eta
    delta_phi = muon_phi - particle_phi
    delta_r = np.sqrt(delta_eta**2 + delta_phi**2)

    # Select particles inside the isolation cone
    in_cone = (delta_r > dr_min) & (delta_r < dr_max)

    # Sum the momentum of particles inside the cone
    cone_p = ak.sum(ak.where(in_cone, particle_p, 0), axis=2)

    # Return the relative cone isolation
    return cone_p / ak.where(muon_p != 0, muon_p, np.nan)


# ---------- User-defined collections ----------


def particle_collections(events):
    # Get reconstructed particles
    particles = events.ReconstructedParticles

    # Get indices for selected particles
    muon_indices = events.Muon_objIdx.index
    electron_indices = events.Electron_objIdx.index
    photon_indices = events.Photon_objIdx.index

    # Create selected particle collections
    muons = particles[muon_indices]
    electrons = particles[electron_indices]
    photons = particles[photon_indices]

    return {
        "Muon": muons,
        "Electron": electrons,
        "Photon": photons,
    }


def particle_track_information(events):
    # Get previously created particle collections
    muons = events.Muon
    electrons = events.Electron

    # Retrieve track states for selected particles
    muon_track_states = track_information(muons)
    electron_track_states = track_information(electrons)

    # Add transverse and longitudinal impact parameters
    muons = ak.with_field(muons, muon_track_states.D0, "d0")
    muons = ak.with_field(muons, muon_track_states.Z0, "z0")
    electrons = ak.with_field(electrons, electron_track_states.D0, "d0")
    electrons = ak.with_field(electrons, electron_track_states.Z0, "z0")

    # Track state covariance matrix (21 elements)
    muon_cov = muon_track_states.covMatrix
    electron_cov = electron_track_states.covMatrix

    # Add the uncertainties
    # FCCAnalyses uses covariance element 0 for D0 and 9 for Z0
    # https://github.com/HEP-FCC/FCCAnalyses/blob/master/analyzers/dataframe/src/ReconstructedParticle2Track.cc
    muons = ak.with_field(muons, np.sqrt(muon_cov[:, :, 0]), "d0Error")
    muons = ak.with_field(muons, np.sqrt(muon_cov[:, :, 9]), "z0Error")
    electrons = ak.with_field(electrons,
                              np.sqrt(electron_cov[:, :, 0]), "d0Error")
    electrons = ak.with_field(electrons,
                              np.sqrt(electron_cov[:, :, 9]), "z0Error")

    return {
        "Muon": muons,
        "Electron": electrons,
    }


def muon_isolation(events):
    # Get previously created muon collection
    muons = events.Muon

    # Add the relative cone isolation
    muons = ak.with_field(muons, calculate_muon_isolation(muons, events),
                          "isolation")

    return {
        "Muon": muons,
}


# Return missing energy vector, based on reco particles
def missing_energy(events):
    particles = events.ReconstructedParticles

    # The first two MC particles correspond to the incoming beam
    beam_particles = events.Particle[:, :2]
    # Compute the center-of-mass energy from the beam particles
    beam_energy = np.sqrt(beam_particles.px**2 + beam_particles.py**2 +
                          beam_particles.pz**2 + beam_particles.mass**2)

    ecm = ak.sum(beam_energy, axis=1)

    missing = ak.zip({
        "px": -ak.sum(particles.px, axis=1),
        "py": -ak.sum(particles.py, axis=1),
        "pz": -ak.sum(particles.pz, axis=1),
        "energy": ecm - ak.sum(particles.energy, axis=1),
    })

    return {
        "MissingEnergy": missing,
    }


def event_information(events):
    return {
        "EventInfo": ak.zip({
            "event": ak.firsts(events.EventHeader.eventNumber),
            "run": ak.firsts(events.EventHeader.runNumber),
            "weight": ak.firsts(events.EventHeader.weight),
            "nTrack": ak.num(events.EFlowTrack, axis=1),
        })
    }
