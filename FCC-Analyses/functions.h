// Example helper functions for defining additional particle collections
// Code adapted from various FCCAnalyses examples and functions
#ifndef EDM4HEPCOLUMNAR_FUNCTIONS_H
#define EDM4HEPCOLUMNAR_FUNCTIONS_H

#include <cmath>
#include <vector>

#include "ROOT/RVec.hxx"
#include "edm4hep/ReconstructedParticleData.h"

namespace EDM4hepColumnar {

// Adapted from FCCAnalyses/analyzers/dataframe/src/ReconstructedParticleSource.cc
// to operate directly on edm4hep::ReconstructedParticleCollection

// Return px
ROOT::VecOps::RVec<float>
getPx(const edm4hep::ReconstructedParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());

    for (const auto &particle : inColl) {
        result.push_back(
            particle.getMomentum().x
        );
    }

    return result;
}

// Return py
ROOT::VecOps::RVec<float>
getPy(const edm4hep::ReconstructedParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());

    for (const auto &particle : inColl) {
        result.push_back(
            particle.getMomentum().y
        );
    }

    return result;
}

// Return pz
ROOT::VecOps::RVec<float>
getPz(const edm4hep::ReconstructedParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());

    for (const auto &particle : inColl) {
        result.push_back(
            particle.getMomentum().z
        );
    }

    return result;
}

// Return polar angle
ROOT::VecOps::RVec<float>
getTheta(const edm4hep::ReconstructedParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());

    for (const auto &particle : inColl) {
        const auto momentum = particle.getMomentum();
        result.push_back(
            std::atan2(
                std::sqrt(momentum.x * momentum.x + momentum.y * momentum.y),
                momentum.z
            )
        );
    }

    return result;
}

// Return azimuthal angle
ROOT::VecOps::RVec<float>
getPhi(const edm4hep::ReconstructedParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());

    for (const auto &particle : inColl) {
        const auto momentum = particle.getMomentum();
        result.push_back(
            std::atan2(momentum.y, momentum.x)
        );
    }

    return result;
}

// Adapted from FCCAnalyses/analyzers/dataframe/src/ReconstructedParticle.cc
// Return goodnessOfPID
ROOT::VecOps::RVec<float>
getGoodnessOfPID(
    const edm4hep::ReconstructedParticleCollection &inColl
) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());

    for (const auto &particle : inColl) {
        result.push_back(
            particle.getGoodnessOfPID()
        );
    }

    return result;
}

// Adapted from FCCAnalyses/examples/FCCee/higgs/mass_xsec/functions.h
// to operate directly on edm4hep::ReconstructedParticleCollection

// Return cone isolation
ROOT::VecOps::RVec<float>
getIsolation(
    const edm4hep::ReconstructedParticleCollection &particles,
    const edm4hep::ReconstructedParticleCollection &allParticles,
    float dr_min = 0.01,
    float dr_max = 0.5
) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(particles.size());
    for (const auto &particle : particles) {
        const auto momentum = particle.getMomentum();
        ROOT::Math::PxPyPzEVector particle_vector(
            momentum.x,
            momentum.y,
            momentum.z,
            particle.getEnergy()
        );

        float momentum_sum = 0.0;
        for (const auto &other : allParticles) {
            const auto other_momentum = other.getMomentum();

            ROOT::Math::PxPyPzEVector other_vector(
                other_momentum.x,
                other_momentum.y,
                other_momentum.z,
                other.getEnergy()
            );

            const double delta_eta = particle_vector.Eta() - other_vector.Eta();
            const double delta_phi =  particle_vector.Phi() - other_vector.Phi();
            const double delta_r = std::sqrt(
                delta_eta * delta_eta + delta_phi * delta_phi
            );

            if (delta_r > dr_min && delta_r < dr_max) {
                momentum_sum += other_vector.P();
            }
        }

        result.push_back(
            momentum_sum / particle_vector.P()
        );
    }

    return result;
}

// Return d0
ROOT::VecOps::RVec<float>
getD0(const edm4hep::ReconstructedParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());
    for (const auto &particle : inColl) {
        const auto tracks = particle.getTracks();

        if (tracks.empty()) {
            result.push_back(-9.);
            continue;
        }

        const auto trackStates = tracks[0].getTrackStates();

        if (trackStates.empty()) {
            result.push_back(-9.);
            continue;
        }

        result.push_back(trackStates[0].D0);
    }

    return result;
}

// Return z0
ROOT::VecOps::RVec<float>
getZ0(const edm4hep::ReconstructedParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());
    for (const auto &particle : inColl) {
        const auto tracks = particle.getTracks();
        if (tracks.empty()) {
            result.push_back(-9.);
            continue;
        }
        const auto trackStates = tracks[0].getTrackStates();
        if (trackStates.empty()) {
            result.push_back(-9.);
            continue;
        }
        result.push_back(trackStates[0].Z0);
    }

    return result;
}


// Adapted from FCCAnalyses/analyzers/dataframe/src/ReconstructedParticle2Track.cc
// Return d0 uncertainty
ROOT::VecOps::RVec<float>
getD0Error(const edm4hep::ReconstructedParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());

    for (const auto &particle : inColl) {
        const auto tracks = particle.getTracks();

        if (tracks.empty()) {
            result.push_back(-9.);
            continue;
        }

        const auto trackStates = tracks[0].getTrackStates();

        if (trackStates.empty()) {
            result.push_back(-9.);
            continue;
        }

        result.push_back(
            std::sqrt(trackStates[0].covMatrix[0])
        );
    }

    return result;
}

// Return z0 uncertainty
ROOT::VecOps::RVec<float>
getZ0Error(const edm4hep::ReconstructedParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());

    for (const auto &particle : inColl) {
        const auto tracks = particle.getTracks();

        if (tracks.empty()) {
            result.push_back(-9.);
            continue;
        }

        const auto trackStates = tracks[0].getTrackStates();

        if (trackStates.empty()) {
            result.push_back(-9.);
            continue;
        }

        result.push_back(
            std::sqrt(trackStates[0].covMatrix[9])
        );
    }

    return result;
}


// Adapted from FCCAnalyses/examples/FCCee/higgs/mass_xsec/functions.h
// to operate directly on edm4hep::ReconstructedParticleCollection

// Compute the missing energy
edm4hep::ReconstructedParticleCollection
getMissingEnergy(
    float ecm,
    const edm4hep::ReconstructedParticleCollection &inColl,
    float p_cutoff = 0.0
) {
    float px = 0.0;
    float py = 0.0;
    float pz = 0.0;
    float energy = 0.0;

    for (const auto &particle : inColl) {
        const auto momentum = particle.getMomentum();

        const float pt = std::sqrt(
            momentum.x * momentum.x
            + momentum.y * momentum.y
        );

        if (pt < p_cutoff) {
            continue;
        }

        px -= momentum.x;
        py -= momentum.y;
        pz -= momentum.z;
        energy += particle.getEnergy();
    }

    edm4hep::ReconstructedParticleCollection result;
    auto missing = result.create();
    missing.setMomentum(
        edm4hep::Vector3f{
            px,
            py,
            pz,
        }
    );

    missing.setEnergy(ecm - energy);
    return result;
}


// Adapted from FCCAnalyses/analyzers/dataframe/src/MCParticle.cc
// to operate directly on edm4hep::MCParticleCollection

// Return the energy calculated from momentum and mass
ROOT::VecOps::RVec<float>
getEnergy(const edm4hep::MCParticleCollection &inColl) {
    ROOT::VecOps::RVec<float> result;
    result.reserve(inColl.size());

    for (const auto &particle : inColl) {
        const auto momentum = particle.getMomentum();
        const auto mass = particle.getMass();

        const float energy = std::sqrt(
            momentum.x * momentum.x
            + momentum.y * momentum.y
            + momentum.z * momentum.z
            + mass * mass
        );

        result.push_back(energy);
    }

    return result;
}

}  // namespace EDM4hepColumnar

#endif
