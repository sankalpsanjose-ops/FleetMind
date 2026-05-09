import type { BoardSize, Difficulty, AIMode, AIProvider } from '../../types/game'
import type { CreateGameParams } from '../../api/client'

interface Props {
  onStart: (params: CreateGameParams) => void
  loading: boolean
}

const BOARD_OPTIONS: { value: BoardSize; label: string; desc: string }[] = [
  { value: 'standard', label: '10×10', desc: 'Standard' },
  { value: 'large',    label: '15×15', desc: 'Large' },
  { value: 'massive',  label: '20×20', desc: 'Massive' },
]

const DIFFICULTY_OPTIONS: { value: Difficulty; label: string; coverage: string }[] = [
  { value: 'cadet',       label: 'Cadet',       coverage: '22%' },
  { value: 'commander',   label: 'Commander',   coverage: '17%' },
  { value: 'admiral',     label: 'Admiral',     coverage: '15%' },
  { value: 'war_veteran', label: 'War Veteran', coverage: '13%' },
  { value: 'black_ops',   label: 'Black Ops',   coverage: '10%' },
  { value: 'armada',      label: 'Armada',      coverage: '20%+' },
  { value: 'guerrilla',   label: 'Guerrilla',   coverage: 'Asymmetric' },
]

const AI_PROVIDERS: { value: AIProvider; label: string }[] = [
  { value: 'anthropic', label: 'Claude (Anthropic)' },
  { value: 'openai',    label: 'GPT-4o (OpenAI)' },
]

const AI_MODES: { value: AIMode; label: string; desc: string }[] = [
  { value: 'pure', label: 'Pure AI',  desc: 'LLM strategy only' },
  { value: 'ml',   label: 'AI + ML',  desc: 'LLM + Q-Learning heatmap' },
]

import { useState } from 'react'

export function ModeSelector({ onStart, loading }: Props) {
  const [mode, setMode] = useState<'human_vs_ai' | 'ai_vs_ai'>('human_vs_ai')
  const [board, setBoard] = useState<BoardSize>('standard')
  const [difficulty, setDifficulty] = useState<Difficulty>('commander')
  const [provider1, setProvider1] = useState<AIProvider>('anthropic')
  const [provider2, setProvider2] = useState<AIProvider>('openai')
  const [aiMode1, setAiMode1] = useState<AIMode>('pure')
  const [aiMode2, setAiMode2] = useState<AIMode>('pure')
  const [showReasoning, setShowReasoning] = useState(false)

  const handleStart = () => {
    const params: CreateGameParams = {
      board_size: board,
      difficulty,
      player1_type: mode === 'human_vs_ai' ? 'human' : 'ai',
      player2_type: 'ai',
      ai_provider_1: mode === 'ai_vs_ai' ? provider1 : undefined,
      ai_mode_1: mode === 'ai_vs_ai' ? aiMode1 : undefined,
      ai_provider_2: provider2,
      ai_mode_2: aiMode2,
      show_reasoning: showReasoning,
    }
    onStart(params)
  }

  return (
    <div className="cyber-panel p-6 flex flex-col gap-6 max-w-lg mx-auto">
      <div>
        <div className="hud-label mb-2">Game Mode</div>
        <div className="flex gap-3">
          {(['human_vs_ai', 'ai_vs_ai'] as const).map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`cyber-btn flex-1 ${mode === m ? 'bg-cyber-cyan text-cyber-bg' : ''}`}
            >
              {m === 'human_vs_ai' ? 'Human vs AI' : 'AI vs AI'}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="hud-label mb-2">Board Size</div>
        <div className="flex gap-2">
          {BOARD_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setBoard(opt.value)}
              className={`cyber-btn flex-1 ${board === opt.value ? 'bg-cyber-cyan text-cyber-bg' : ''}`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="hud-label mb-2">Difficulty</div>
        <div className="grid grid-cols-4 gap-1">
          {DIFFICULTY_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setDifficulty(opt.value)}
              title={`Fleet coverage: ${opt.coverage}`}
              className={`px-2 py-1 border text-[10px] uppercase tracking-wider transition-all
                ${difficulty === opt.value
                  ? 'border-cyber-cyan text-cyber-bg bg-cyber-cyan'
                  : 'border-cyber-border text-cyber-dim hover:border-cyber-cyan hover:text-cyber-cyan'
                }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {mode === 'ai_vs_ai' && (
        <div className="grid grid-cols-2 gap-4">
          <ProviderPicker
            label="Player 1 AI"
            provider={provider1} onProvider={setProvider1}
            aiMode={aiMode1} onMode={setAiMode1}
          />
          <ProviderPicker
            label="Player 2 AI"
            provider={provider2} onProvider={setProvider2}
            aiMode={aiMode2} onMode={setAiMode2}
          />
        </div>
      )}

      {mode === 'human_vs_ai' && (
        <ProviderPicker
          label="Opponent AI"
          provider={provider2} onProvider={setProvider2}
          aiMode={aiMode2} onMode={setAiMode2}
        />
      )}

      <label className="flex items-center gap-3 cursor-pointer">
        <div
          onClick={() => setShowReasoning(v => !v)}
          className={`w-10 h-5 border rounded-full relative transition-all ${
            showReasoning ? 'border-cyber-cyan bg-cyber-cyan/20' : 'border-cyber-border'
          }`}
        >
          <div className={`absolute top-0.5 w-4 h-4 rounded-full transition-all ${
            showReasoning ? 'right-0.5 bg-cyber-cyan' : 'left-0.5 bg-cyber-dim'
          }`} />
        </div>
        <span className="hud-label">Show AI Reasoning</span>
      </label>

      <button
        onClick={handleStart}
        disabled={loading}
        className="cyber-btn w-full py-3 text-sm"
      >
        {loading ? 'Initializing...' : 'Deploy Fleet'}
      </button>
    </div>
  )
}

function ProviderPicker({
  label, provider, onProvider, aiMode, onMode
}: {
  label: string
  provider: AIProvider
  onProvider: (p: AIProvider) => void
  aiMode: AIMode
  onMode: (m: AIMode) => void
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="hud-label">{label}</div>
      {AI_PROVIDERS.map(p => (
        <button
          key={p.value}
          onClick={() => onProvider(p.value)}
          className={`cyber-btn text-left px-3 py-1.5 text-[10px] ${provider === p.value ? 'bg-cyber-blue/20 border-cyber-blue text-cyber-blue' : ''}`}
        >
          {p.label}
        </button>
      ))}
      <div className="flex gap-1 mt-1">
        {AI_MODES.map(m => (
          <button
            key={m.value}
            onClick={() => onMode(m.value)}
            title={m.desc}
            className={`flex-1 px-2 py-1 border text-[9px] uppercase tracking-wider transition-all
              ${aiMode === m.value
                ? 'border-cyber-cyan text-cyber-bg bg-cyber-cyan'
                : 'border-cyber-border text-cyber-dim hover:border-cyber-cyan'
              }`}
          >
            {m.label}
          </button>
        ))}
      </div>
    </div>
  )
}
