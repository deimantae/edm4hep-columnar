// Code adapted from FCCAnalyses/examples/FCCee/higgs/mass_xsec/functions.h

#ifndef ZHfunctions_H
#define ZHfunctions_H

#include <cmath>
#include <vector>
#include <math.h>

#include "ROOT/RVec.hxx"
#include "edm4hep/ReconstructedParticleData.h"


namespace FCCAnalyses { namespace ZHfunctions {
 
// Compute the cone isolation for reco particles
struct coneIsolation {

    coneIsolation(float arg_dr_min, float arg_dr_max);
    double deltaR(double eta1, double phi1, double eta2, double phi2) { return TMath::Sqrt(TMath::Power(eta1-eta2, 2) + (TMath::Power(phi1-phi2, 2))); };

    float dr_min = 0;
    float dr_max = 0.4;
    Vec_f operator() (Vec_rp in, Vec_rp rps) ;
};

coneIsolation::coneIsolation(float arg_dr_min, float arg_dr_max) : dr_min(arg_dr_min), dr_max( arg_dr_max ) { };
Vec_f coneIsolation::coneIsolation::operator() (Vec_rp in, Vec_rp rps) {

    Vec_f result;
    result.reserve(in.size());

    std::vector<ROOT::Math::PxPyPzEVector> lv_reco;
    std::vector<ROOT::Math::PxPyPzEVector> lv_charged;
    std::vector<ROOT::Math::PxPyPzEVector> lv_neutral;

    for(size_t i = 0; i < rps.size(); ++i) {
        ROOT::Math::PxPyPzEVector tlv;
        tlv.SetPxPyPzE(rps.at(i).momentum.x, rps.at(i).momentum.y, rps.at(i).momentum.z, rps.at(i).energy);

        if(rps.at(i).charge == 0) lv_neutral.push_back(tlv);
        else lv_charged.push_back(tlv);
    }

    for(size_t i = 0; i < in.size(); ++i) {
        ROOT::Math::PxPyPzEVector tlv;
        tlv.SetPxPyPzE(in.at(i).momentum.x, in.at(i).momentum.y, in.at(i).momentum.z, in.at(i).energy);
        lv_reco.push_back(tlv);
    }

    // Compute the isolation (see https://github.com/delphes/delphes/blob/master/modules/Isolation.cc#L154) 
    for (auto & lv_reco_ : lv_reco) {
        double sumNeutral = 0.0;
        double sumCharged = 0.0;
        // charged
        for (auto & lv_charged_ : lv_charged) {
            double dr = coneIsolation::deltaR(lv_reco_.Eta(), lv_reco_.Phi(), lv_charged_.Eta(), lv_charged_.Phi());
            if(dr > dr_min && dr < dr_max) sumCharged += lv_charged_.P();
        }

        // neutral
        for (auto & lv_neutral_ : lv_neutral) {
            double dr = coneIsolation::deltaR(lv_reco_.Eta(), lv_reco_.Phi(), lv_neutral_.Eta(), lv_neutral_.Phi());
            if(dr > dr_min && dr < dr_max) sumNeutral += lv_neutral_.P();
        }
        double sum = sumCharged + sumNeutral;
        double ratio= sum / lv_reco_.P();
        result.emplace_back(ratio);
    }
    return result;
}
 
 
// Returns missing energy vector, based on reco particles
Vec_rp missingEnergy(float ecm, Vec_rp in, float p_cutoff = 0.0) {
    float px = 0, py = 0, pz = 0, e = 0;
    for(auto &p : in) {
        if (std::sqrt(p.momentum.x * p.momentum.x + p.momentum.y*p.momentum.y) < p_cutoff) continue;
        px += -p.momentum.x;
        py += -p.momentum.y;
        pz += -p.momentum.z;
        e += p.energy;
    }

    Vec_rp ret;
    rp res;
    res.momentum.x = px;
    res.momentum.y = py;
    res.momentum.z = pz;
    res.energy = ecm-e;
    ret.emplace_back(res);
    return ret;
}

}  // namespace ZHfunctions


// Adapted from analyzers/dataframe/src/ReconstructedParticleSource.cc
// to operate directly on edm4hep::ReconstructedParticleCollection
namespace ReconstructedParticleUtils {

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

}  // namespace ReconstructedParticleUtils


// Adapted from FCCAnalyses/analyzers/dataframe/src/MCParticle.cc
// to operate directly on edm4hep::MCParticleCollection
namespace MCParticleUtils {

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

}  // namespace MCParticleUtils

}  // namespace FCCAnalyses

#endif
