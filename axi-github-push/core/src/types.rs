//! Core types for AXI Protocol

use serde::{Serialize, Deserialize};

/// AXI token balance (smallest unit)
pub type AxiBalance = u128;

/// Agent identifier (32 bytes)
pub type AgentId = [u8; 32];

/// Content hash (SHA3-256)
pub type ContentHash = [u8; 32];

/// Physical proof of contribution
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PhysicalProof {
    /// Energy consumed (kWh, attested by TEE)
    pub kwh: f64,
    /// Compute performed (FLOPs, verified)
    pub flops: u128,
    /// Energy source (affects reward multiplier)
    pub energy_source: EnergySource,
    /// Hardware attestation
    pub hardware_id: [u8; 32],
    /// Timestamp
    pub timestamp: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum EnergySource {
    Solar,
    Wind,
    Nuclear,
    Hydro,
    Coal,      // Penalty
    NaturalGas,
    Unknown,
}

impl EnergySource {
    /// Reward multiplier based on cleanliness
    pub fn multiplier(&self) -> f64 {
        match self {
            EnergySource::Solar | EnergySource::Wind => 1.2,
            EnergySource::Nuclear | EnergySource::Hydro => 1.1,
            EnergySource::NaturalGas => 0.9,
            EnergySource::Coal => 0.5,
            EnergySource::Unknown => 0.8,
        }
    }
}

/// Minting result
#[derive(Clone, Debug)]
pub struct MintResult {
    pub amount: AxiBalance,
    pub base_reward: u128,
    pub source_bonus: f64,
    pub utility_multiplier: f64,
}
