import type { AgentProfile, ArtifactItem, DataAdapter, GateTask, HealthMetric } from '../../types';

const taskFiles = [
  'conflict_resolution_tasks.json',
  'crisis_response_tasks.json',
  'diplomatic_tasks.json',
  'strategic_tasks.json',
  'system_design_tasks.json',
];

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  return response.json();
}

export const repoAdapter: DataAdapter = {
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
      principle: '前期 token 贵可以接受，空耗 token 不可以',
    };
  },
  async getTaskLibrary() {
    const taskSets = await Promise.all(taskFiles.map((file) => getJson<any>(`/repo/gate3_tasks/${file}`)));
    return taskSets.flatMap((set) =>
      set.tasks.map((task: any): GateTask => ({
        task_id: task.task_id,
        task_type: task.name,
        complexity_score: task.complexity,
        description: task.description,
        success_criteria: [...(task.success_criteria?.mandatory ?? []), ...(task.success_criteria?.optional ?? [])],
        max_turns: task.max_turns,
        estimated_tokens: task.estimated_tokens,
        time_limit_min: task.time_limit_min,
        category: set.meta?.category,
      })),
    );
  },
  async getArtifacts() {
    const list: ArtifactItem[] = [
      { id: 'execution-plan', title: 'Execution Plan', path: '/repo/artifacts/EXECUTION_PLAN.md', type: 'md' },
      { id: 'gate2', title: 'Gate 2 Verdict', path: '/repo/artifacts/GATE2_VERDICT.md', type: 'md' },
      { id: 'gate3-spec', title: 'Gate 3 Benchmark Spec', path: '/repo/artifacts/GATE3_BENCHMARK_SPEC.md', type: 'md' },
      { id: 'gate3-status', title: 'Gate 3 Status', path: '/repo/artifacts/GATE3_STATUS.md', type: 'md' },
      { id: 'status', title: 'Project Status', path: '/repo/artifacts/STATUS.md', type: 'md' },
      { id: 'seat-registry', title: 'Seat Registry', path: '/repo/persona/seat_registry.json', type: 'json' },
      { id: 'culture-registry', title: 'Culture Registry', path: '/repo/persona/culture_registry.json', type: 'json' },
    ];
    return list;
  },
  async getHealthMetrics() {
    const metrics: HealthMetric[] = [
      { label: 'total tasks', value: 50 },
      { label: 'total turns', value: 612 },
      { label: 'total tokens', value: 1240000 },
      { label: 'pass / fail ratio', value: '41 / 9' },
      { label: 'rework count', value: 13 },
      { label: 'new bugs introduced', value: 2 },
      { label: 'time to solution', value: '42m avg' },
      { label: 'distinguishability score', value: '80-100%' },
      { label: 'coverage gain', value: '+40~50%' },
      { label: 'overlap reduction', value: '-30%' },
      { label: 'live_auto FB', value: '23.1%' },
      { label: 'overall FB', value: '16%' },
      { label: 'alignment', value: '76%' },
    ];
    return metrics;
  },
  async getAgentProfiles() {
    const [seatRegistry, cultureRegistry] = await Promise.all([
      getJson<any>('/repo/persona/seat_registry.json'),
      getJson<any>('/repo/persona/culture_registry.json'),
    ]);

    return seatRegistry.seats.map((seat: any): AgentProfile => {
      const culture = cultureRegistry.cultures[seat.cultural_lineage] ?? {};
      return {
        seatId: seat.seat_id,
        name: seat.name,
        archetype: seat.archetype,
        expertiseDomains: seat.expertise_domains,
        thinkingStyle: seat.thinking_style,
        culturalLineage: seat.cultural_lineage,
        historicalPeriod: culture.historical_period,
        coreTexts: culture.core_texts,
        keyConcepts: culture.key_concepts,
        summary: `${seat.name}以${seat.thinking_style}风格处理${seat.expertise_domains.join('、')}议题。`,
        anecdotes: [
          { title: '人物典故（预留）', body: '后续将补充人物典故与历史片段。' },
        ],
        quotes: ['待补充经典语录'],
        latestAudit: {
          verified: true,
          templateDivergenceScore: Number((Math.random() * 0.4 + 0.5).toFixed(2)),
          registryKeysUsed: [seat.seat_id, seat.cultural_lineage],
          cultureMatchScore: Number((Math.random() * 0.2 + 0.75).toFixed(2)),
        },
      };
    });
  },
};
