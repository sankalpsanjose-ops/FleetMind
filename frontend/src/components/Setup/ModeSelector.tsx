import { useState } from 'react'
import type { BoardSize, Difficulty, AIMode, AIProvider } from '../../types/game'
import type { CreateGameParams } from '../../api/client'

interface Props {
  onStart: (params: CreateGameParams) => void
  loading: boolean
}

const BOARD_OPTIONS: { value: BoardSize; label: string }[] = [
  { value: 'standard', label: '10×10' },
  { value: 'large',    label: '15×15' },
  { value: 'massive',  label: '20×20' },
]

const DIFFICULTY_OPTIONS: { value: Difficulty; label: string; tip: string }[] = [
  { value: 'cadet',       label: 'Cadet',       tip: '22% — random fire' },
  { value: 'commander',   label: 'Commander',   tip: '17% — hunt & target' },
  { value: 'admiral',     label: 'Admiral',     tip: '15% — parity + gap' },
  { value: 'war_veteran', label: 'War Veteran', tip: '13% — bias learning' },
  { value: 'black_ops',   label: 'Black Ops',   tip: '10% — max RL weight' },
  { value: 'armada',      label: 'Armada',      tip: '20%+ — large fleet' },
  { value: 'guerrilla',   label: 'Guerrilla',   tip: 'Asymmetric fleet' },
]

interface ModelOption { id: string; label: string; tag: string }

const ANTHROPIC_MODELS: ModelOption[] = [
  { id: 'claude-opus-4-7',  label: 'Opus 4.7',   tag: 'Thinking' },
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
  { value: 'pure', label: 'Pure AI',  desc: 'LLM only' },
  { value: 'ml',   label: 'AI + ML',  desc: 'LLM + heatmap' },
]

export function ModeSelector({ onStart, loading }: Props) {
  const [mode,         setMode]         = useState<'human_vs_ai' | 'ai_vs_ai'>('human_vs_ai')
  const [board,        setBoard]        = useState<BoardSize>('standard')
  const [difficulty,   setDifficulty]   = useState<Difficulty>('commander')
  const [provider1,    setProvider1]    = useState<AIProvider>('anthropic')
  const [model1,       setModel1]       = useState(DEFAULT_MODELS.anthropic)
  const [aiMode1,      setAiMode1]      = useState<AIMode>('pure')
  const [provider2,    setProvider2]    = useState<AIProvider>('openai')
  const [model2,       setModel2]       = useState(DEFAULT_MODELS.openai)
  const [aiMode2,      setAiMode2]      = useState<AIMode>('pure')
  const [showReasoning, setShowReasoning] = useState(false)

  const handleProvider1Change = (p: AIProvider) => {
    setProvider1(p)
    setModel1(DEFAULT_MODELS[p])
  }
  const handleProvider2Change = (p: AIProvider) => {
    setProvider2(p)
    setModel2(DEFAULT_MODELS[p])
  }

  const handleStart = () => {
    onStart({
      board_size: board,
      difficulty,
      player1_type: mode === 'human_vs_ai' ? 'human' : 'ai',
      player2_type: 'ai',
      ai_provider_1: mode === 'ai_vs_ai' ? provider1 : undefined,
      ai_mode_1:     mode === 'ai_vs_ai' ? aiMode1   : undefined,
      ai_model_1:    mode === 'ai_vs_ai' ? model1     : undefined,
      ai_provider_2: provider2,
      ai_mode_2:     aiMode2,
      ai_model_2:    model2,
      show_reasoning: showReasoning,
    })
  }

  return (
    <div className="cyber-panel p-6 flex flex-col gap-5 w-full max-w-lg mx-auto">

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
        <div className="hud-label mb-2">Difficulty</div>
        <div className="grid grid-cols-4 gap-1">
          {DIFFICULTY_OPTIONS.map(opt => (
            <button key={opt.value} onClick={() => setDifficulty(opt.value)} title={opt.tip}
              className={`px-2 py-1.5 border text-[10px] uppercase tracking-wider transition-all
                ${difficulty === opt.value
                  ? 'border-cyber-cyan bg-cyber-cyan text-cyber-bg'
                  : 'border-cyber-border text-cyber-dim hover:border-cyber-cyan hover:text-cyber-cyan'
                }`}>
              {opt.label}
            </button>
          ))}
        </div>
        <div className="hud-label mt-1 text-[9px]">
          {DIFFICULTY_OPTIONS.find(o => o.value === difficulty)?.tip}
        </div>
      </div>

      {/* AI configuration */}
      {mode === 'ai_vs_ai' ? (
        <div className="grid grid-cols-2 gap-4">
          <ProviderPicker label="Player 1 AI"
            provider={provider1} onProvider={handleProvider1Change}
            model={model1} onModel={setModel1}
            aiMode={aiMode1} onMode={setAiMode1} />
          <ProviderPicker label="Player 2 AI"
            provider={provider2} onProvider={handleProvider2Change}
            model={model2} onModel={setModel2}
            aiMode={aiMode2} onMode={setAiMode2} />
        </div>
      ) : (
        <ProviderPicker label="Opponent AI"
          provider={provider2} onProvider={handleProvider2Change}
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
        {showReasoning && <span className="text-[9px] text-cyber-dim">(Opus thinking visible)</span>}
      </label>

      <button onClick={handleStart} disabled={loading} className="cyber-btn w-full py-3 text-sm">
        {loading ? 'Initializing...' : 'Deploy Fleet'}
      </button>
    </div>
  )
}

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

      {/* Provider toggle */}
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

      {/* Model picker */}
      <div className="flex flex-col gap-1">
        {models.map(m => (
          <button key={m.id} onClick={() => onModel(m.id)}
            className={`flex items-center justify-between px-2 py-1.5 border text-[10px] transition-all
              ${model === m.id
                ? 'border-cyber-cyan bg-cyber-cyan/10 text-cyber-cyan'
                : 'border-cyber-border text-cyber-dim hover:border-cyber-cyan/50'
              }`}>
            <span>{m.label}</span>
            <span className={`text-[9px] px-1 rounded ${
              m.tag === 'Thinking' || m.tag === 'Reasoning'
                ? 'text-cyber-orange border border-cyber-orange/40'
                : 'text-cyber-dim border border-cyber-border'
            }`}>{m.tag}</span>
          </button>
        ))}
      </div>

      {/* AI mode */}
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
