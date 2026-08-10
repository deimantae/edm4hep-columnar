"""
Example functions for defining additional particle collections.

Each collection definition specifies:
- how the collection is created from the EDM4hep event,
- how variables are accessed for that collection.
"""

from pathlib import Path

import ROOT

# Local C++ helper functions used for variables not provided
# by FCCAnalyses::PodioSource::ReconstructedParticle
functions_header = Path(__file__).resolve().parent / "functions.h"

ROOT.gInterpreter.Declare(f'#include "{functions_header}"')

# ---------- Helper functions ----------

def reconstructed_particle_expression(collection_name, variable_name):
    # Helpers available through FCCAnalyses::PodioSource::ReconstructedParticle
    helper_names = {
        "p": "getP",
        "pt": "getPt",
        "energy": "getE",
        "mass": "getMass",
        "charge": "getCharge",
    }
    
    # Additional helpers declared in functions.h 
    declared_names = {
        "px": "getPx",
        "py": "getPy",
        "pz": "getPz",
        "theta": "getTheta",
        "phi": "getPhi",
        "goodnessOfPID": "getGoodnessOfPID",
        "d0": "getD0",
        "z0": "getZ0",
        "d0Error": "getD0Error",
        "z0Error": "getZ0Error",
    }

    special_expressions = {
        "isolation": (
            "FCCAnalyses::ReconstructedParticleUtils::getIsolation("
            f"{collection_name}, ReconstructedParticles)"
        ),
    }
    
    if variable_name in special_expressions:
        return special_expressions[variable_name]

    if variable_name in helper_names:
        return (
            "ReconstructedParticle::"
            f"{helper_names[variable_name]}({collection_name})"
        )
    
    if variable_name in declared_names:
        return (
            "FCCAnalyses::ReconstructedParticleUtils::"
            f"{declared_names[variable_name]}({collection_name})"
        )

    raise ValueError(
        f"Unsupported reconstructed particle variable: {variable_name}"
    )
    

def event_information_expression(_, variable_name):
    expressions = {
        "event": "EventHeader.eventNumber()[0]",
        "run": "EventHeader.runNumber()[0]",
        "weight": "EventHeader.weight()[0]",
        "nTrack": "EFlowTrack.size()",
    }

    if variable_name not in expressions:
        raise ValueError(
            f"Unsupported EventInfo variable: {variable_name}"
        )

    return expressions[variable_name]


# ---------- User-defined collections ----------

# Muon, Electron and Photon are already provided as input collections
# by podio::DataSource. Only define how their variables are accessed.
def particle_collections():
    return {
        "Jet": {"expression": reconstructed_particle_expression},
        "Muon": {"expression": reconstructed_particle_expression},
        "Electron": {"expression": reconstructed_particle_expression},
        "Photon": {"expression": reconstructed_particle_expression},
    }


def missing_energy():
    return {
        "ECM": {
            "define": (
                "FCCAnalyses::MCParticleUtils::getEnergy(Particle)[0] + "
                "FCCAnalyses::MCParticleUtils::getEnergy(Particle)[1]"
            ),
        },
        "MissingEnergy": {
            "define": (
                "FCCAnalyses::ReconstructedParticleUtils::"
                "getMissingEnergy(ECM, ReconstructedParticles)"
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
