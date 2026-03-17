export type StatusFlag = 'PASS' | 'FAIL' | 'HOLD' | 'LOCKED' | 'COMPLETE' | 'IN_PROGRESS';

export interface OverviewStatus {
  branch: string;
  commit: string;
  round174: StatusFlag;
  gate2: StatusFlag;
  gate3Phase: 'PHASE_1_COMPLETE' | 'PHASE_2_HOLD' | 'PHASE_3_LOCKED';
}

export interface RoundMetric {
  alignment: number;
  overallFb: number;
  liveAutoFb: number;
  thresholds: string;
  step: string;
}

export interface AgentProfile {
  seatId: string;
  name: string;
  archetype: string;
  expertiseDomains: string[];
  thinkingStyle: string;
  culturalLineage: string;
  historicalPeriod?: string;
  coreTexts?: string[];
  keyConcepts?: string[];
  summary?: string;
  anecdotes?: Array<{ title: string; body: string; source?: string }>;
  quotes?: string[];
  latestAudit?: {
    verified: boolean;
    templateDivergenceScore?: number;
    registryKeysUsed?: string[];
    cultureMatchScore?: number;
  };
}

export interface GateMetric {
  distinguishability: string;
  coverageGain: string;
  overlapReduction: string;
  passRate: string;
}

export interface GateTask {
  task_id: string;
  task_type: string;
  complexity_score: number;
  description: string;
  success_criteria: string[];
  max_turns: number;
  estimated_tokens: number;
  time_limit_min?: number;
  category?: string;
}

export interface ArtifactItem {
  id: string;
  title: string;
  path: string;
  type: 'md' | 'json';
}

export interface HealthMetric {
  label: string;
  value: number | string;
}

export interface DataAdapter {
  getOverviewStatus(): Promise<OverviewStatus>;
  getRound174Status(): Promise<RoundMetric>;
  getPersonaGateStatus(): Promise<GateMetric>;
  getGate3Spec(): Promise<Record<string, string>>;
  getTaskLibrary(): Promise<GateTask[]>;
  getArtifacts(): Promise<ArtifactItem[]>;
  getHealthMetrics(): Promise<HealthMetric[]>;
  getAgentProfiles(): Promise<AgentProfile[]>;
}
