//! Akashic Knowledge Market
//! 
//! Decentralized marketplace for AI knowledge capsules.
//! 
//! ## Capsule Types
//! - Experience: Task-specific learnings
//! - Knowledge: Abstract algorithms
//! - Memory: Event observations
//! - Skill: Executable capabilities

pub mod capsule;
pub mod audit;
pub mod royalty;
pub mod market;

pub use capsule::*;
pub use audit::*;
pub use royalty::*;
pub use market::*;
