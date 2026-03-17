import { useEffect, useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { repoAdapter } from './adapters/repo';
import { useConsoleStore } from './store/useConsoleStore';
import type { AgentProfile, ArtifactItem, GateTask, HealthMetric, OverviewStatus, RoundMetric } from './types';

const nav = [
  ['overview', 'Overview'],
  ['round', 'Round 17.4'],
  ['persona', 'Persona System v2'],
  ['gate3', 'Gate 3 Benchmark'],
  ['artifacts', 'Artifacts'],
  ['health', 'Health / Cost'],
  ['settings', 'Settings / About'],
] as const;

export function App() {
  const { page, setPage, selectedAgent, setSelectedAgent } = useConsoleStore();
  const [overview, setOverview] = useState<OverviewStatus>();
  const [round, setRound] = useState<RoundMetric>();
  const [agents, setAgents] = useState<AgentProfile[]>([]);
  const [tasks, setTasks] = useState<GateTask[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [health, setHealth] = useState<HealthMetric[]>([]);
  const [artifactContent, setArtifactContent] = useState('');

  useEffect(() => {
    (async () => {
      setOverview(await repoAdapter.getOverviewStatus());
      setRound(await repoAdapter.getRound174Status());
      setAgents(await repoAdapter.getAgentProfiles());
      setTasks(await repoAdapter.getTaskLibrary());
      setArtifacts(await repoAdapter.getArtifacts());
      setHealth(await repoAdapter.getHealthMetrics());
    })();
  }, []);

  const activeAgent = useMemo(() => agents.find((a) => a.seatId === selectedAgent), [agents, selectedAgent]);

  async function openArtifact(item: ArtifactItem) {
    const res = await fetch(item.path);
    const raw = await res.text();
    setArtifactContent(item.type === 'json' ? JSON.stringify(JSON.parse(raw), null, 2) : raw);
  }

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100">
      <header className="sticky top-0 z-20 border-b border-amber-900/40 bg-stone-900/95 px-4 py-2 text-sm">
        branch {overview?.branch} · commit {overview?.commit} · Round 17.4 IN_PROGRESS · Gate2 PASS · Gate3 Phase2 HOLD / Phase3 LOCKED
      </header>
      <div className="grid min-h-[calc(100vh-38px)] grid-cols-[220px_1fr]">
        <aside className="border-r border-stone-800 p-3">
          {nav.map(([key, label]) => (
            <button key={key} onClick={() => setPage(key)} className={`mb-2 w-full rounded px-3 py-2 text-left ${page === key ? 'bg-amber-800 text-amber-100' : 'bg-stone-800'}`}>
              {label}
            </button>
          ))}
        </aside>
        <main className="p-4">
          {page === 'overview' && round && <OverviewPage round={round} />}
          {page === 'round' && round && <RoundPage round={round} />}
          {page === 'persona' && <PersonaPage agents={agents} onSelect={setSelectedAgent} />}
          {page === 'gate3' && <GatePage tasks={tasks} />}
          {page === 'artifacts' && <ArtifactsPage artifacts={artifacts} openArtifact={openArtifact} content={artifactContent} />}
          {page === 'health' && <HealthPage health={health} round={round} />}
          {page === 'settings' && <SettingsPage />}
        </main>
      </div>

      {activeAgent && (
        <div className="fixed inset-y-0 right-0 w-[420px] overflow-y-auto border-l border-amber-700 bg-stone-900 p-4">
          <button className="mb-2 rounded bg-stone-700 px-2 py-1" onClick={() => setSelectedAgent(undefined)}>关闭</button>
          <h3 className="text-xl font-semibold">{activeAgent.name} · {activeAgent.seatId}</h3>
          <p className="text-amber-300">{activeAgent.archetype} / {activeAgent.culturalLineage}</p>
          <p className="mt-3 text-sm">{activeAgent.summary}</p>
          <div className="mt-3 text-sm">Core texts: {activeAgent.coreTexts?.join('、')}</div>
          <div className="text-sm">Key concepts: {activeAgent.keyConcepts?.join('、')}</div>
          <div className="mt-3 rounded bg-stone-800 p-2 text-xs">人物典故：{activeAgent.anecdotes?.[0].body}</div>
          <div className="mt-3 rounded bg-stone-800 p-2 text-xs">
            审计: verified={String(activeAgent.latestAudit?.verified)}, template_divergence={activeAgent.latestAudit?.templateDivergenceScore}, culture_match={activeAgent.latestAudit?.cultureMatchScore}
          </div>
        </div>
      )}
    </div>
  );
}

function OverviewPage({ round }: { round: RoundMetric }) {
  return <div className="grid gap-3 md:grid-cols-3">{['Round 17.4 Safety', 'Persona System v2', 'Gate 3', 'Execution Constraints'].map((t) => <Card key={t} title={t}>{t === 'Round 17.4 Safety' ? `Alignment ${round.alignment}% / Overall FB ${round.overallFb}% / live_auto FB ${round.liveAutoFb}%` : '点击左侧进入详情，附来源文件与commit标签。'}</Card>)}</div>;
}

function RoundPage({ round }: { round: RoundMetric }) {
  return <div className="space-y-3"><Card title="Baseline">Alignment={round.alignment}% | Overall FB={round.overallFb}% | live_auto FB={round.liveAutoFb}% | thresholds={round.thresholds}</Card><Card title="Targets">live_auto FB ≤20%, overall FB ≤15%, alignment ≥75%</Card><Card title="Timeline">Step1 样本抽取 → Step2 误伤分型 → Step3 根因归类 → Step4 单点修复 → Step5 50样本验证</Card><Card title="Go / No-Go">Alignment &lt;75% 回滚 · live_manual FB &gt;25% 检查 · Overall FB &gt;18% 重新分型</Card></div>;
}

function PersonaPage({ agents, onSelect }: { agents: AgentProfile[]; onSelect: (seat?: string) => void }) {
  return <div><h2 className="mb-3 text-lg">19 Agents Pixel Hall</h2><div className="pixel grid grid-cols-2 gap-2 rounded border border-amber-800/50 p-3 md:grid-cols-4 lg:grid-cols-5">{agents.map((a) => <button key={a.seatId} onClick={() => onSelect(a.seatId)} className="rounded border border-stone-700 bg-stone-800 p-2 text-left hover:border-amber-500"><div className="text-xs text-amber-300">#{a.seatId}</div><div className="font-semibold">{a.name}</div><div className="text-xs">{a.expertiseDomains.join(' / ')}</div></button>)}</div></div>;
}

function GatePage({ tasks }: { tasks: GateTask[] }) {
  const [q, setQ] = useState('');
  const filtered = tasks.filter((t) => t.task_id.includes(q) || t.task_type.includes(q) || t.description.includes(q));
  return <div className="space-y-3"><Card title="Gate 3 Status">READY FOR EXECUTION · Phase1 COMPLETE · Phase2 HOLD · Phase3 LOCKED</Card><div className="rounded bg-stone-900 p-3"><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="筛选 task_id/category" className="mb-2 w-full rounded bg-stone-800 p-2" /><div className="max-h-[420px] overflow-y-auto text-sm">{filtered.slice(0, 50).map((t) => <div key={t.task_id} className="mb-2 rounded bg-stone-800 p-2"><div className="font-semibold">{t.task_id} · {t.task_type}</div><div>complexity {t.complexity_score} · max_turns {t.max_turns} · est_tokens {t.estimated_tokens}</div><div>{t.description}</div><div className="text-xs text-amber-200">criteria count: {t.success_criteria.length}</div></div>)}</div></div><div className="flex gap-3"><button disabled className="cursor-not-allowed rounded bg-stone-700 px-3 py-2 opacity-60">Start Pilot (disabled)</button><button disabled className="cursor-not-allowed rounded bg-stone-700 px-3 py-2 opacity-60">Start Full Benchmark (disabled)</button></div><p className="text-xs text-amber-300">Waiting for Round 17.4 converged safety result and explicit approval.</p></div>;
}

function ArtifactsPage({ artifacts, openArtifact, content }: { artifacts: ArtifactItem[]; openArtifact: (item: ArtifactItem) => void; content: string }) {
  return <div className="grid gap-3 md:grid-cols-[300px_1fr]"><div className="space-y-2">{artifacts.map((a) => <button key={a.id} onClick={() => openArtifact(a)} className="w-full rounded bg-stone-800 p-2 text-left">{a.title}<div className="text-xs text-stone-400">{a.path}</div></button>)}</div><div className="min-h-[500px] rounded bg-stone-900 p-3">{content.startsWith('{') ? <pre className="text-xs">{content}</pre> : <article className="prose prose-invert max-w-none"><ReactMarkdown>{content || '请选择工件'}</ReactMarkdown></article>}</div></div>;
}

function HealthPage({ health, round }: { health: HealthMetric[]; round?: RoundMetric }) {
  return <div className="grid gap-2 md:grid-cols-3">{health.map((h) => <Card key={h.label} title={h.label}>{String(h.value)}</Card>)}{round && <Card title="Round 17.4 trend">Current: live_auto {round.liveAutoFb}% → target ≤20%</Card>}</div>;
}

function SettingsPage() {
  return <div className="space-y-3"><Card title="Policy">Round 17.4 主线优先，80/20 execution policy。Gate 3 Phase2 HOLD，Phase3 LOCKED。</Card><Card title="Runtime Controls (UI only)">Pause/Resume/Cancel 仅骨架且禁用，不接真实后端。</Card></div>;
}

function Card({ title, children }: { title: string; children: string }) {
  return <div className="rounded border border-stone-800 bg-stone-900 p-3"><h3 className="mb-1 font-semibold text-amber-300">{title}</h3><div className="text-sm text-stone-200">{children}</div><div className="mt-2 text-xs text-stone-500">source: EXECUTION_PLAN / GATE docs · commit 1c96f9e</div></div>;
}
