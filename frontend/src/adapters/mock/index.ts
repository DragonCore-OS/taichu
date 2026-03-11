import type { DataAdapter } from '../../types';

export const mockAdapter: DataAdapter = {
  async getOverviewStatus() {
    return {
      branch: 'main',
      commit: '1c96f9e',
      round174: 'IN_PROGRESS',
      gate2: 'PASS',
      gate3Phase: 'PHASE_2_HOLD',
    };
  },
  async getRound174Status() {
    return {
      alignment: 76,
      overallFb: 16,
      liveAutoFb: 23.1,
      thresholds: 'deliberation 70 / review 80',
      step: 'Step 3 根因归类',
    };
  },
  async getPersonaGateStatus() {
    return {
      distinguishability: '80-100%',
      coverageGain: '+40%~+50%',
      overlapReduction: '-30%',
      passRate: '9/9 PASS',
    };
  },
  async getGate3Spec() {
    return {
      phase1: 'COMPLETE',
      phase2: 'HOLD',
      phase3: 'LOCKED',
      principle: 'Token 可贵，空耗不可',
    };
  },
  async getTaskLibrary() {
    return [];
  },
  async getArtifacts() {
    return [];
  },
  async getHealthMetrics() {
    return [];
  },
  async getAgentProfiles() {
    return [];
  },
};
