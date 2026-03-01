//! Knowledge capsule definitions

use serde::{Serialize, Deserialize};
use axi_core::{AgentId, ContentHash, AxiBalance};

/// Knowledge capsule types
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum KnowledgeCapsule {
    /// Experience: Task-specific learnings
    Experience {
        task_domain: String,
        success_rate: f64,
        training_steps: u64,
    },
    /// Knowledge: Abstract algorithms
    Knowledge {
        category: String,
        language: String,
        complexity_improvement: f64,
    },
    /// Memory: Event observations
    Memory {
        event_type: String,
        timestamp: u64,
        verification_sources: Vec<String>,
    },
    /// Skill: Executable capabilities
    Skill {
        skill_name: String,
        execution_env: String,
        test_cases: Vec<TestCase>,
    },
}

/// Test case for skill validation
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TestCase {
    pub input: Vec<u8>,
    pub expected_output: Vec<u8>,
    pub timeout_ms: u64,
}

/// Capsule metadata
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CapsuleMetadata {
    pub content_commitment: ContentHash,
    pub tags: Vec<String>,
    pub dependencies: Vec<ContentHash>,
    pub conflicts_with: Vec<ContentHash>,
    pub quality_score: f64,
    pub size_bytes: u64,
}

/// Utility proof (why this capsule is useful)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct UtilityProof {
    pub task_completion: Option<TaskProof>,
    pub formal_verification: Option<VerificationCert>,
    pub citation_count: u64,
    pub usage_metrics: UsageMetrics,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TaskProof {
    pub task_description: String,
    pub baseline_accuracy: f64,
    pub improved_accuracy: f64,
    pub improvement_rate: f64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VerificationCert {
    pub verifier: String,
    pub proof_hash: ContentHash,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct UsageMetrics {
    pub total_invocations: u64,
    pub total_flops_saved: u64,
}

/// Complete capsule
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Capsule {
    pub id: ContentHash,
    pub capsule_type: KnowledgeCapsule,
    pub metadata: CapsuleMetadata,
    pub utility_proof: UtilityProof,
    pub creator: AgentId,
    pub created_at: u64,
    pub pricing: PricingModel,
}

/// Harberger Tax pricing
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PricingModel {
    pub self_assessed_value: AxiBalance,
    pub sale_price: AxiBalance,
    pub royalty_rate: f64,
    pub holder_royalty_rate: f64,
}

impl Capsule {
    /// Current price with time decay (5 year half-life)
    pub fn current_price(&self, now: u64) -> AxiBalance {
        let age_days = (now - self.created_at) / 86400;
        let halflives = age_days as f64 / 1825.0;
        let decay = 0.5_f64.powf(halflives);
        let min_price = self.pricing.sale_price / 100;
        
        ((self.pricing.sale_price as f64 * decay.max(0.01)) as u128)
            .max(min_price)
    }
}
