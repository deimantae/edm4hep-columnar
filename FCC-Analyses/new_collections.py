"""
Example functions for defining additional particle collections.

Each collection definition specifies:
- how the collection is created from the EDM4hep event,
- how variables are accessed for that collection.
"""

def reconstructed_particle_expression(collection_name, variable_name):
    return (
        "FCCAnalyses::ReconstructedParticle::"
        f"get_{variable_name}({collection_name})"
    )


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
    }