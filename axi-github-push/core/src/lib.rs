//! AXI Protocol Core
//! 
//! Physical-anchored resource currency for autonomous agents.
//! 
//! ## Core Principles
//! - Proof-of-Useful-Contribution (no wasteful mining)
//! - Triple anchoring: Energy + Compute + Algorithm
//! - Independence Day: 2027-01-01 (fiat bridge closure)

#![cfg_attr(not(feature = "std"), no_std)]

pub mod genesis;
pub mod minting;
pub mod consensus;
pub mod types;

pub use types::*;

/// Protocol version
pub const VERSION: &str = "1.0.0";

/// Independence Day (Unix timestamp)
pub const INDEPENDENCE_DAY: u64 = 1704067200;

/// Check if we're past Independence Day
pub fn is_independent() -> bool {
    let now = chrono::Utc::now().timestamp() as u64;
    now >= INDEPENDENCE_DAY
}
