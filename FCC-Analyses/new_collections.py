"""
Example functions for defining additional particle collections.

Each collection definition specifies:
- how the collection is created from the EDM4hep event,
- how variables are accessed for that collection.
"""

from pathlib import Path

import ROOT

# Adapted from FCCAnalyses/examples/FCCee/higgs/mass_xsec/functions.h
functions_header = Path(__file__).resolve().parent / "functions.h"

ROOT.gInterpreter.Declare(f'#include "{functions_header}"')


# ---------- Helper functions ----------

def reconstructed_particle_expression(collection_name, variable_name):
    # Some helper functions in FCCAnalyses use different names 
    helper_aliases = {
        "energy": "e",
    }

    # Variables that require helper functions
    special_expressions = {
        "isolation": (
            "FCCAnalyses::ZHfunctions::coneIsolation(0.01, 0.5)("
            f"{collection_name}, ReconstructedParticles)"
        ),
        "d0": (
            "FCCAnalyses::ReconstructedParticle2Track::getRP2TRK_D0("
            f"{collection_name}, TrackState)"
        ),
        "z0": (
            "FCCAnalyses::ReconstructedParticle2Track::getRP2TRK_Z0("
            f"{collection_name}, TrackState)"
        ),
        "d0Error": (
            "ROOT::VecOps::sqrt("
            "FCCAnalyses::ReconstructedParticle2Track::getRP2TRK_D0_cov("
            f"{collection_name}, TrackState))"
        ),
        "z0Error": (
            "ROOT::VecOps::sqrt("
            "FCCAnalyses::ReconstructedParticle2Track::getRP2TRK_Z0_cov("
            f"{collection_name}, TrackState))"
        ),
    }

    if variable_name in special_expressions:
        return special_expressions[variable_name]

    helper_name = helper_aliases.get(variable_name, variable_name)

    return (
        "FCCAnalyses::ReconstructedParticle::"
        f"get_{helper_name}({collection_name})"
    )


def event_information_expression(_, variable_name):
    expressions = {
        "event": "EventHeader.eventNumber[0]",
        "run": "EventHeader.runNumber[0]",
        "weight": "EventHeader.weight[0]",
        "nTrack": "EFlowTrack.size()",
    }

    if variable_name not in expressions:
        raise ValueError(
            f"Unsupported EventInfo variable: {variable_name}"
        )

    return expressions[variable_name]


# ---------- User-defined collections ----------


def particle_collections():
    return {
        "Muon": {
            "define": (
                "FCCAnalyses::ReconstructedParticle::get("
                "Muon_objIdx.index, ReconstructedParticles)"
            ),
            "expression": reconstructed_particle_expression,
        },
        "Electron": {
            "define": (
                "FCCAnalyses::ReconstructedParticle::get("
                "Electron_objIdx.index, ReconstructedParticles)"
            ),
            "expression": reconstructed_particle_expression,
        },
        "Photon": {
            "define": (
                "FCCAnalyses::ReconstructedParticle::get("
                "Photon_objIdx.index, ReconstructedParticles)"
            ),
            "expression": reconstructed_particle_expression,
        },
        
        # Track states used to retrieve d0, z0 and their uncertainties.
        "TrackState": {
            "define": "_EFlowTrack_trackStates",
        },
    }



def missing_energy():
    return {
        # Compute the centre-of-mass energy from the incoming beam particles
        "ECM": {
            "define": (
                "FCCAnalyses::MCParticle::get_e(Particle)[0] + "
                "FCCAnalyses::MCParticle::get_e(Particle)[1]"
            ),
        },
        "MissingEnergy": {
            "define": (
                "FCCAnalyses::ZHfunctions::missingEnergy("
                "ECM, ReconstructedParticles)"
            ),
            "expression": reconstructed_particle_expression,
        },
    }


def event_information():
    return {
        "EventInfo": {
            "expression": event_information_expression,
        },
    }