import type { GameState } from '../../types/game'

interface Props {
  state: GameState | null
  isAiThinking: boolean
  difficulty: string
  boardSize: number
}

const PHASE_LABELS = {
  setup: 'Initializing',
  placement: 'Fleet Placement',
  battle: 'Battle',
  game_over: 'Game Over',
}

export function StatusBar({ state, isAiThinking, difficulty, boardSize }: Props) {
  if (!state) return null

  const phase = PHASE_LABELS[state.phase] ?? state.phase
  const turn = state.current_turn === 'player1' ? 'P1' : 'P2'
  const isOver = state.phase === 'game_over'

  return (
    <div className="flex items-center gap-6 px-4 py-2 border-b border-cyber-border text-xs">
      {/* Phase */}
      <div className="flex flex-col">
        <span className="hud-label">Phase</span>
        <span className={`hud-value ${isOver ? 'text-cyber-orange' : 'text-cyber-cyan'} animate-flicker`}>
          {phase}
        </span>
      </div>

      {/* Turn */}
      {state.phase === 'battle' && (
        <div className="flex flex-col">
          <span className="hud-label">Turn</span>
          <span className="hud-value">#{state.turn_number} — {turn}</span>
        </div>
      )}

      {/* AI thinking indicator */}
      {isAiThinking && (
        <div className="flex items-center gap-2 text-cyber-blue">
          <div className="flex gap-0.5">
            {[0,1,2].map(i => (
              <div
                key={i}
                className="w-1 h-1 rounded-full bg-cyber-blue animate-pulse"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
          <span className="hud-label text-cyber-blue">AI Computing</span>
        </div>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Meta */}
      <div className="flex gap-4">
        <div className="flex flex-col items-end">
          <span className="hud-label">Board</span>
          <span className="hud-value">{boardSize}×{boardSize}</span>
        </div>
        <div className="flex flex-col items-end">
          <span className="hud-label">Difficulty</span>
          <span className="hud-value uppercase">{difficulty}</span>
        </div>
      </div>

      {/* Winner banner */}
      {isOver && state.winner && (
        <div className="flex flex-col items-end">
          <span className="hud-label">Winner</span>
          <span className="text-cyber-orange font-bold uppercase text-shadow-cyan animate-flicker">
            {state.winner === 'player1' ? 'Player 1' : 'Player 2'}
          </span>
        </div>
      )}
    </div>
  )
}
