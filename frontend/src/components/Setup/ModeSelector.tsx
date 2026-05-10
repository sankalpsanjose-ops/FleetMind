import { useState } from 'react'
import type { BoardSize, Difficulty, AIMode, AIProvider } from '../../types/game'
import type { CreateGameParams } from '../../api/client'

interface Props {
  onStart: (params: CreateGameParams) => void
  loading: boolean
}

// ── Difficulty data ──────────────────────────────────────────────────────────

interface ShipEntry { name: string; size: number; count: number }
interface DifficultyBriefing {
  label: string
  threat: number           // 1–5
  coverage: string
  fleet: ShipEntry[]
  strategy: string
  mlHeatmap: number        // 0–100
  mlRL: number             // 0–100
  gap: boolean             // 1-cell gap required
  note?: string
}

const BRIEFINGS: Record<Difficulty, DifficultyBriefing> = {
  cadet: {
    label: 'Cadet', threat: 1, coverage: '22%',
    fleet: [
      { name: 'Carrier',    size: 5, count: 2 },
      { name: 'Battleship', size: 4, count: 2 },
      { name: 'Cruiser',    size: 3, count: 1 },
    ],
    strategy: 'Fires completely at random. No pattern recognition, no targeting. '
      + 'Large fleet makes it easy to score hits — ideal for learning the controls.',
    mlHeatmap: 0, mlRL: 0, gap: false,
    note: 'AI makes no LLM calls — pure random.choice(). Zero latency per turn.',
  },
  commander: {
    label: 'Commander', threat: 2, coverage: '17%',
    fleet: [
      { name: 'Carrier',    size: 5, count: 1 },
      { name: 'Battleship', size: 4, count: 1 },
      { name: 'Cruiser',    size: 3, count: 1 },
      { name: 'Submarine',  size: 3, count: 1 },
      { name: 'Patrol',     size: 2, count: 1 },
    ],
    strategy: 'Classic hunt & target. Parity-filtered scanning in hunt mode — '
      + 'only fires on cells that could contain the smallest remaining ship. '
      + 'Locks onto hit axis to sink before resuming hunt.',
    mlHeatmap: 100, mlRL: 0, gap: false,
  },
  admiral: {
    label: 'Admiral', threat: 3, coverage: '15%',
    fleet: [
      { name: 'Battleship', size: 4, count: 1 },
      { name: 'Cruiser',    size: 3, count: 1 },
      { name: 'Submarine',  size: 3, count: 1 },
      { name: 'Patrol',     size: 2, count: 2 },
    ],
    strategy: 'Full probability density analysis. Counts valid ship placements '
      + 'through every cell and fires where they converge. Strict axis-locking '
      + 'after hits. Smaller fleet spread thinner — harder to find.',
    mlHeatmap: 80, mlRL: 20, gap: true,
    note: 'Ships are placed with a 1-cell gap — they will never be adjacent.',
  },
  war_veteran: {
    label: 'War Veteran', threat: 3, coverage: '13%',
    fleet: [
      { name: 'Cruiser',   size: 3, count: 1 },
      { name: 'Submarine', size: 3, count: 1 },
      { name: 'Frigate',   size: 3, count: 1 },
      { name: 'Patrol',    size: 2, count: 2 },
      { name: 'Speedboat', size: 2, count: 2 },
      { name: 'Corvette',  size: 2, count: 1 },
    ],
    strategy: 'Probability heatmap blended with Q-learning from past matches. '
      + 'The RL agent learns where human players tend to hide ships over time — '
      + 'edges, corners, and horizontal-bias patterns are exploited.',
    mlHeatmap: 60, mlRL: 40, gap: true,
    note: 'Gets harder as more matches are played — RL agent retains history across sessions.',
  },
  black_ops: {
    label: 'Black Ops', threat: 5, coverage: '10%',
    fleet: [
      { name: 'Submarine', size: 3, count: 1 },
      { name: 'Frigate',   size: 3, count: 1 },
      { name: 'Patrol',    size: 2, count: 2 },
      { name: 'Speedboat', size: 2, count: 2 },
      { name: 'Corvette',  size: 2, count: 2 },
    ],
    strategy: 'RL-dominant targeting with reinforced constraint propagation. '
      + 'Only 11 cells to find on a 100-cell board. The Q-learning agent '
      + 'prioritises cells that have historically concealed small ships. '
      + 'Surgical, relentless, and extremely hard to survive.',
    mlHeatmap: 30, mlRL: 70, gap: true,
    note: 'Fewest cells to sink but hardest to hide — smallest ships can squeeze anywhere.',
  },
  armada: {
    label: 'Armada', threat: 2, coverage: '22%',
    fleet: [
      { name: 'Carrier',    size: 5, count: 2 },
      { name: 'Battleship', size: 4, count: 2 },
      { name: 'Cruiser',    size: 3, count: 1 },
      { name: 'Submarine',  size: 3, count: 1 },
    ],
    strategy: 'Heavy fleet — probability targeting optimised for large-ship '
      + 'detection. High coverage means more hits early, but you have many '
      + 'ships to sink. Great for fast, action-heavy games.',
    mlHeatmap: 80, mlRL: 20, gap: false,
    note: 'More ships = more events = longer games. Expect 60–120 turns.',
  },
  guerrilla: {
    label: 'Guerrilla', threat: 4, coverage: 'Asymmetric',
    fleet: [
      { name: 'Carrier (P1)',  size: 5, count: 1 },
      { name: 'Patrol (P2)',   size: 2, count: 2 },
      { name: 'Corvette (P2)', size: 2, count: 3 },
    ],
    strategy: 'Asymmetric warfare. Player 1 fields a single Carrier; Player 2 '
      + 'fields a swarm of small ships totalling similar area. Carrier hunter '
      + 'uses long scan lines; swarm hunter applies strict parity to find '
      + '2-cell targets hiding in any corner.',
    mlHeatmap: 100, mlRL: 0, gap: true,
    note: 'Fleet composition differs per side — the AI adapts its prompt and heatmap accordingly.',
  },
}

const BOARD_OPTIONS: { value: BoardSize; label: string }[] = [
  { value: 'standard', label: '10×10' },
  { value: 'large',    label: '15×15' },
  { value: 'massive',  label: '20×20' },
]

const DIFFICULTY_LIST = Object.keys(BRIEFINGS) as Difficulty[]

interface ModelOption { id: string; label: string; tag: string }

const ANTHROPIC_MODELS: ModelOption[] = [
  { id: 'claude-opus-4-7',   label: 'Opus 4.7',   tag: 'Thinking' },
  { id: 'claude-sonnet-4-6', label: 'Sonnet 4.6', tag: 'Fast' },
]
const OPENAI_MODELS: ModelOption[] = [
  { id: 'o4-mini', label: 'o4-mini', tag: 'Reasoning' },
  { id: 'gpt-4o',  label: 'GPT-4o',  tag: 'Fast' },
]
const PROVIDER_MODELS: Record<AIProvider, ModelOption[]> = {
  anthropic: ANTHROPIC_MODELS,
  openai:    OPENAI_MODELS,
}
const DEFAULT_MODELS: Record<AIProvider, string> = {
  anthropic: 'claude-opus-4-7',
  openai:    'o4-mini',
}
const AI_MODES: { value: AIMode; label: string; desc: string }[] = [
  { value: 'pure', label: 'Pure AI', desc: 'LLM only' },
  { value: 'ml',   label: 'AI + ML', desc: 'LLM + heatmap' },
]

// ── Component ────────────────────────────────────────────────────────────────

export function ModeSelector({ onStart, loading }: Props) {
  const [mode,          setMode]          = useState<'human_vs_ai' | 'ai_vs_ai'>('human_vs_ai')
  const [board,         setBoard]         = useState<BoardSize>('standard')
  const [difficulty,    setDifficulty]    = useState<Difficulty>('commander')
  const [provider1,     setProvider1]     = useState<AIProvider>('anthropic')
  const [model1,        setModel1]        = useState(DEFAULT_MODELS.anthropic)
  const [aiMode1,       setAiMode1]       = useState<AIMode>('pure')
  const [provider2,     setProvider2]     = useState<AIProvider>('openai')
  const [model2,        setModel2]        = useState(DEFAULT_MODELS.openai)
  const [aiMode2,       setAiMode2]       = useState<AIMode>('pure')
  const [showReasoning, setShowReasoning] = useState(false)

  const b = BRIEFINGS[difficulty]

  const handleProvider1 = (p: AIProvider) => { setProvider1(p); setModel1(DEFAULT_MODELS[p]) }
  const handleProvider2 = (p: AIProvider) => { setProvider2(p); setModel2(DEFAULT_MODELS[p]) }

  const handleStart = () => onStart({
    board_size:     board,
    difficulty,
    player1_type:   mode === 'human_vs_ai' ? 'human' : 'ai',
    player2_type:   'ai',
    ai_provider_1:  mode === 'ai_vs_ai' ? provider1 : undefined,
    ai_mode_1:      mode === 'ai_vs_ai' ? aiMode1   : undefined,
    ai_model_1:     mode === 'ai_vs_ai' ? model1     : undefined,
    ai_provider_2:  provider2,
    ai_mode_2:      aiMode2,
    ai_model_2:     model2,
    show_reasoning: showReasoning,
  })

  return (
    <div className="cyber-panel p-4 flex flex-col gap-3 w-full max-w-lg mx-auto">

      {/* Mode */}
      <div>
        <div className="hud-label mb-2">Game Mode</div>
        <div className="flex gap-3">
          {(['human_vs_ai', 'ai_vs_ai'] as const).map(m => (
            <button key={m} onClick={() => setMode(m)}
              className={`cyber-btn flex-1 ${mode === m ? 'bg-cyber-cyan text-cyber-bg' : ''}`}>
              {m === 'human_vs_ai' ? 'Human vs AI' : 'AI vs AI'}
            </button>
          ))}
        </div>
      </div>

      {/* Board */}
      <div>
        <div className="hud-label mb-2">Board Size</div>
        <div className="flex gap-2">
          {BOARD_OPTIONS.map(opt => (
            <button key={opt.value} onClick={() => setBoard(opt.value)}
              className={`cyber-btn flex-1 ${board === opt.value ? 'bg-cyber-cyan text-cyber-bg' : ''}`}>
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Difficulty */}
      <div>
        <div className="hud-label mb-1.5">Difficulty</div>
        <div className="grid grid-cols-4 gap-1 mb-2">
          {DIFFICULTY_LIST.map(d => (
            <button key={d} onClick={() => setDifficulty(d)}
              className={`px-2 py-1.5 border text-[10px] uppercase tracking-wider transition-all
                ${difficulty === d
                  ? 'border-cyber-cyan bg-cyber-cyan text-cyber-bg'
                  : 'border-cyber-border text-cyber-dim hover:border-cyber-cyan hover:text-cyber-cyan'
                }`}>
              {BRIEFINGS[d].label}
            </button>
          ))}
        </div>
        <MissionBriefing b={b} />
      </div>

      {/* AI config */}
      {mode === 'ai_vs_ai' ? (
        <div className="grid grid-cols-2 gap-4">
          <ProviderPicker label="Player 1 AI"
            provider={provider1} onProvider={handleProvider1}
            model={model1} onModel={setModel1}
            aiMode={aiMode1} onMode={setAiMode1} />
          <ProviderPicker label="Player 2 AI"
            provider={provider2} onProvider={handleProvider2}
            model={model2} onModel={setModel2}
            aiMode={aiMode2} onMode={setAiMode2} />
        </div>
      ) : (
        <ProviderPicker label="Opponent AI"
          provider={provider2} onProvider={handleProvider2}
          model={model2} onModel={setModel2}
          aiMode={aiMode2} onMode={setAiMode2} />
      )}

      {/* Reasoning toggle */}
      <label className="flex items-center gap-3 cursor-pointer" onClick={() => setShowReasoning(v => !v)}>
        <div className={`w-10 h-5 border rounded-full relative transition-all shrink-0
          ${showReasoning ? 'border-cyber-cyan bg-cyber-cyan/20' : 'border-cyber-border'}`}>
          <div className={`absolute top-0.5 w-4 h-4 rounded-full transition-all
            ${showReasoning ? 'right-0.5 bg-cyber-cyan' : 'left-0.5 bg-cyber-dim'}`} />
        </div>
        <span className="hud-label">Show AI Reasoning</span>
        {showReasoning && <span className="text-[9px] text-cyber-dim">(Opus: thinking chain visible)</span>}
      </label>

      <button onClick={handleStart} disabled={loading} className="cyber-btn w-full py-3 text-sm">
        {loading ? 'Initializing...' : 'Deploy Fleet'}
      </button>
    </div>
  )
}

// ── Mission Briefing ─────────────────────────────────────────────────────────

function MissionBriefing({ b }: { b: DifficultyBriefing }) {
  const threatColor = b.threat >= 5 ? 'text-cyber-red' :
                      b.threat >= 4 ? 'text-cyber-orange' :
                      b.threat >= 3 ? 'text-yellow-400' :
                      'text-cyber-cyan'

  return (
    <div className="border border-cyber-border bg-[#010d18] p-3 text-[10px] leading-relaxed font-mono">

      {/* Stats row */}
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-cyber-border/50">
        <div className="flex items-center gap-1.5">
          <span className="hud-label">Coverage</span>
          <span className="text-cyber-cyan font-bold text-xs">{b.coverage}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="hud-label">Threat</span>
          <div className="flex gap-0.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className={`w-2.5 h-2.5 border ${
                i < b.threat
                  ? `${threatColor} bg-current border-transparent`
                  : 'border-cyber-border/40'
              }`} />
            ))}
          </div>
        </div>
      </div>

      {/* Fleet */}
      <div className="mb-2">
        <div className="hud-label mb-1">Fleet Composition</div>
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {b.fleet.map((ship, i) => (
            <div key={i} className="flex items-center gap-1.5">
              {ship.count > 1 && (
                <span className="text-cyber-dim">{ship.count}×</span>
              )}
              <span className="text-cyber-cyan">{ship.name}</span>
              <div className="flex gap-0.5">
                {Array.from({ length: ship.size }).map((_, j) => (
                  <div key={j} className="w-2 h-2 bg-cyber-cyan/70 border border-cyber-cyan/40" />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Strategy */}
      <div className="mb-2">
        <div className="hud-label mb-1">AI Strategy</div>
        <p className="text-cyber-dim leading-snug">{b.strategy}</p>
      </div>

      {/* ML Intel */}
      <div className="mb-2">
        <div className="hud-label mb-1">ML Intel</div>
        <div className="flex flex-col gap-1">
          <Bar label="Heatmap" value={b.mlHeatmap} color="bg-cyber-cyan" />
          <Bar label="Q-Learn" value={b.mlRL}      color="bg-cyber-orange" />
        </div>
      </div>

      {/* Rules row */}
      <div className="flex items-center gap-4 pt-1.5 border-t border-cyber-border/50">
        <div className="flex items-center gap-1.5">
          <div className={`w-1.5 h-1.5 rounded-full ${b.gap ? 'bg-cyber-orange' : 'bg-cyber-dim'}`} />
          <span className={b.gap ? 'text-cyber-orange' : 'text-cyber-dim'}>
            {b.gap ? '1-cell gap enforced' : 'Ships may touch'}
          </span>
        </div>
        {b.note && (
          <span className="text-cyber-dim italic truncate flex-1">↳ {b.note}</span>
        )}
      </div>
    </div>
  )
}

function Bar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-cyber-dim w-14 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-cyber-border/30 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${value}%` }} />
      </div>
      <span className="text-cyber-dim w-8 text-right">{value}%</span>
    </div>
  )
}

// ── Provider Picker ──────────────────────────────────────────────────────────

function ProviderPicker({ label, provider, onProvider, model, onModel, aiMode, onMode }: {
  label: string
  provider: AIProvider
  onProvider: (p: AIProvider) => void
  model: string
  onModel: (m: string) => void
  aiMode: AIMode
  onMode: (m: AIMode) => void
}) {
  const models = PROVIDER_MODELS[provider]
  return (
    <div className="flex flex-col gap-2">
      <div className="hud-label">{label}</div>
      <div className="flex gap-1">
        {(['anthropic', 'openai'] as AIProvider[]).map(p => (
          <button key={p} onClick={() => onProvider(p)}
            className={`flex-1 px-2 py-1 border text-[10px] uppercase tracking-wider transition-all
              ${provider === p
                ? 'border-cyber-blue bg-cyber-blue/20 text-cyber-blue'
                : 'border-cyber-border text-cyber-dim hover:border-cyber-blue'
              }`}>
            {p === 'anthropic' ? 'Claude' : 'GPT'}
          </button>
        ))}
      </div>
      <div className="flex flex-col gap-1">
        {models.map(m => (
          <button key={m.id} onClick={() => onModel(m.id)}
            className={`flex items-center justify-between px-2 py-1.5 border text-[10px] transition-all
              ${model === m.id
                ? 'border-cyber-cyan bg-cyber-cyan/10 text-cyber-cyan'
                : 'border-cyber-border text-cyber-dim hover:border-cyber-cyan/50'
              }`}>
            <span>{m.label}</span>
            <span className={`text-[9px] px-1 rounded border ${
              m.tag === 'Thinking' || m.tag === 'Reasoning'
                ? 'text-cyber-orange border-cyber-orange/40'
                : 'text-cyber-dim border-cyber-border'
            }`}>{m.tag}</span>
          </button>
        ))}
      </div>
      <div className="flex gap-1">
        {AI_MODES.map(m => (
          <button key={m.value} onClick={() => onMode(m.value)} title={m.desc}
            className={`flex-1 px-2 py-1 border text-[9px] uppercase tracking-wider transition-all
              ${aiMode === m.value
                ? 'border-cyber-cyan bg-cyber-cyan text-cyber-bg'
                : 'border-cyber-border text-cyber-dim hover:border-cyber-cyan'
              }`}>
            {m.label}
          </button>
        ))}
      </div>
    </div>
  )
}
