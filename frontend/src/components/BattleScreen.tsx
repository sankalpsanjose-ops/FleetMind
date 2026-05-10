import { useState, useCallback, useEffect, useRef } from 'react'
import { useGame } from '../hooks/useGame'
import { useSound } from '../hooks/useSound'
import { gameApi, type CreateGameParams } from '../api/client'
import { GameBoard } from './GameBoard/GameBoard'
import { StatusBar } from './HUD/StatusBar'
import { ShotLog } from './HUD/ShotLog'
import { ReasoningPanel } from './HUD/ReasoningPanel'
import { ModeSelector } from './Setup/ModeSelector'
import { FleetPlacement } from './Setup/FleetPlacement'
import type { ShipPlacement } from '../types/game'

const BOARD_SIZE_MAP = { standard: 10, large: 15, massive: 20 }

const MODEL_SHORT: Record<string, string> = {
  'claude-opus-4-7':   'Opus 4.7',
  'claude-sonnet-4-6': 'Sonnet 4.6',
  'claude-haiku-4-5':  'Haiku 4.5',
  'gpt-4o':            'GPT-4o',
  'o4-mini':           'o4-mini',
  'o3-mini':           'o3-mini',
  'o1':                'o1',
}

function fmtModel(provider?: string, model?: string): string {
  const p = provider === 'anthropic' ? 'Claude' : provider === 'openai' ? 'GPT' : 'AI'
  const m = model ? (MODEL_SHORT[model] ?? model) : ''
  return m ? `${p} · ${m}` : p
}

export function BattleScreen() {
  const game = useGame()
  const { playHit, playMiss, playSunk, playVictory, playDefeat } = useSound()
  const [starting, setStarting] = useState(false)
  const [showReasoning, setShowReasoning] = useState(false)
  const [boardSizeNum, setBoardSizeNum] = useState(10)
  const [difficulty, setDifficulty] = useState('commander')
  const [mode, setMode] = useState<'human_vs_ai' | 'ai_vs_ai'>('human_vs_ai')
  const [playerFleet, setPlayerFleet] = useState<Record<string, boolean>>({})
  const [confirmForfeit, setConfirmForfeit] = useState(false)
  const [p1Label, setP1Label] = useState('Player 1')
  const [p2Label, setP2Label] = useState('AI')
  const aiStartedRef = useRef(false)
  const prevLogLenRef = useRef(0)
  const prevPhaseRef = useRef<string | undefined>(undefined)

  const isHumanTurn = game.state?.phase === 'battle' &&
    game.state.current_turn === 'player1' &&
    mode === 'human_vs_ai'

  // Mark AI as started when the WS enters battle phase (server auto-starts the loop)
  useEffect(() => {
    if (mode === 'ai_vs_ai' && game.state?.phase === 'battle') {
      aiStartedRef.current = true
    }
  }, [mode, game.state?.phase]) // eslint-disable-line

  // Sound: play on each new shot log entry
  useEffect(() => {
    const len = game.log.length
    if (len > prevLogLenRef.current) {
      const latest = game.log[len - 1]
      if (latest.result === 'sunk')     playSunk()
      else if (latest.result === 'hit') playHit()
      else                              playMiss()
      prevLogLenRef.current = len
    }
  }, [game.log.length]) // eslint-disable-line

  // Sound: victory / defeat on game over
  useEffect(() => {
    const phase = game.state?.phase
    if (phase === 'game_over' && prevPhaseRef.current !== 'game_over') {
      if (game.state?.winner === 'player1') playVictory()
      else                                  playDefeat()
    }
    prevPhaseRef.current = phase
  }, [game.state?.phase]) // eslint-disable-line

  const handleModeStart = useCallback(async (params: CreateGameParams) => {
    setStarting(true)
    aiStartedRef.current = false
    const isAiVsAi = params.player1_type === 'ai'
    setBoardSizeNum(BOARD_SIZE_MAP[params.board_size])
    setDifficulty(params.difficulty)
    setMode(isAiVsAi ? 'ai_vs_ai' : 'human_vs_ai')
    // Build readable player labels
    setP1Label(isAiVsAi ? fmtModel(params.ai_provider_1, params.ai_model_1) : 'You')
    setP2Label(fmtModel(params.ai_provider_2, params.ai_model_2))
    // AI vs AI always shows reasoning; human games respect the toggle
    const showReason = isAiVsAi ? true : (params.show_reasoning ?? false)
    setShowReasoning(showReason)
    try {
      await game.createGame({ ...params, show_reasoning: showReason })
    } finally {
      setStarting(false)
    }
  }, [game])

  const handlePlacementConfirm = useCallback(async (placements: ShipPlacement[]) => {
    // Build a cell lookup so GameBoard can show player's own fleet during battle
    const SIZES: Record<string, number> = { carrier: 5, battleship: 4, cruiser: 3, submarine: 3, patrol: 2 }
    const fleet: Record<string, boolean> = {}
    for (const p of placements) {
      const size = SIZES[p.ship_type] ?? 3
      for (let i = 0; i < size; i++) {
        const r = p.orientation === 'horizontal' ? p.row : p.row + i
        const c = p.orientation === 'horizontal' ? p.col + i : p.col
        fleet[`${r},${c}`] = true
      }
    }
    setPlayerFleet(fleet)
    await game.placeFleet(placements)
  }, [game])

  const handleCellClick = useCallback((row: number, col: number) => {
    if (!isHumanTurn) return
    game.humanFire(row, col)
  }, [isHumanTurn, game])

  const handleReset = useCallback(() => {
    game.resetGame()
    setPlayerFleet({})
    setShowReasoning(false)
    setConfirmForfeit(false)
    setP1Label('Player 1')
    setP2Label('AI')
    aiStartedRef.current    = false
    prevLogLenRef.current   = 0
    prevPhaseRef.current    = undefined
  }, [game])

  const handleForfeit = useCallback(async () => {
    await game.forfeit()
    setPlayerFleet({})
    setShowReasoning(false)
    setConfirmForfeit(false)
    aiStartedRef.current    = false
    prevLogLenRef.current   = 0
    prevPhaseRef.current    = undefined
  }, [game])

  // ── No game yet: show mode selector
  if (!game.gameId || !game.state) {
    return (
      <div className="min-h-full bg-cyber-bg relative overflow-hidden">

        {/* Captain's deck video background — drop any .mp4 into frontend/public/ and update src */}
        <video
          src="/captain-deck.mp4"
          autoPlay loop muted playsInline
          className="absolute inset-0 w-full h-full object-cover opacity-40 pointer-events-none"
          onError={e => { (e.currentTarget as HTMLVideoElement).style.display = 'none' }}
        />
        {/* gradient vignette so edges stay dark */}
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse at center, transparent 50%, #000510 90%)' }} />

        {/* Scrollable content — min-h-full + justify-center centres when it fits;
            outer overflow-y-auto scrolls when it doesn't */}
        <div className="absolute inset-0 z-10 overflow-y-auto">
          <div className="flex flex-col items-center justify-center min-h-full py-6 px-8">
            <div className="mb-5 text-center">
              <div className="text-5xl mb-2 select-none animate-pulse-glow inline-block"
                style={{ textShadow: '0 0 24px rgba(0,255,180,0.7), 0 0 8px rgba(0,255,180,0.9)' }}>
                ⚓
              </div>
              <h1 className="text-4xl font-bold text-shadow-cyan mb-1.5 animate-flicker">
                FLEET<span className="text-cyber-blue">MIND</span>
              </h1>
              <div className="hud-label tracking-[0.6em]">AI Battleship · Combat Simulator</div>
            </div>
            <ModeSelector onStart={handleModeStart} loading={starting} />
            {game.error && (
              <div className="mt-4 px-4 py-2 border border-cyber-red text-cyber-red text-xs">
                {game.error}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ── Human placement phase
  if (game.state.phase === 'placement' && mode === 'human_vs_ai') {
    return (
      <div className="flex flex-col items-center justify-center min-h-full p-8 bg-cyber-bg">
        <FleetPlacement
          boardSize={boardSizeNum}
          onConfirm={handlePlacementConfirm}
        />
        {game.error && (
          <div className="mt-4 px-4 py-2 border border-cyber-red text-cyber-red text-xs">
            {game.error}
          </div>
        )}
      </div>
    )
  }

  // ── Battle / Game Over
  return (
    <div className="flex flex-col h-full overflow-hidden bg-cyber-bg">
      <StatusBar
        state={game.state}
        isAiThinking={game.isAiThinking}
        difficulty={difficulty}
        boardSize={boardSizeNum}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — P1 reasoning (AI vs AI only) */}
        {mode === 'ai_vs_ai' && showReasoning && (
          <div className="flex flex-col w-52 border-r border-cyber-border p-2 overflow-hidden shrink-0">
            <ReasoningPanel
              log={game.log}
              show={showReasoning}
              side="player1"
              label={`P1 · ${p1Label}`}
            />
          </div>
        )}

        {/* Boards */}
        <div className="flex flex-1 items-center justify-center gap-6 p-4">
          <div className="flex-1 max-w-[480px]">
            <GameBoard
              boardSize={boardSizeNum}
              attackGrid={game.state.attack_grid.player1}
              side="player1"
              label={mode === 'human_vs_ai' ? '[ YOUR SHOTS ]' : `[ P1 · ${p1Label} ]`}
              active={game.state.phase === 'battle' && game.state.current_turn === 'player1'}
              onCellClick={handleCellClick}
              interactive={isHumanTurn}
            />
          </div>
          <div className="flex-1 max-w-[480px]">
            <GameBoard
              boardSize={boardSizeNum}
              attackGrid={game.state.attack_grid.player2}
              ownFleetGrid={mode === 'human_vs_ai' ? playerFleet : undefined}
              side="player2"
              label={mode === 'human_vs_ai' ? `[ ENEMY · ${p2Label} ]` : `[ P2 · ${p2Label} ]`}
              active={game.state.phase === 'battle' && game.state.current_turn === 'player2'}
            />
          </div>
        </div>

        {/* Right sidebar */}
        <div className="flex flex-col w-56 border-l border-cyber-border p-3 gap-3 overflow-hidden shrink-0">
          <ShotLog log={game.log} />

          {showReasoning && (
            <div className="flex-1 min-h-0">
              <ReasoningPanel
                log={game.log}
                show={showReasoning}
                side={mode === 'ai_vs_ai' ? 'player2' : 'all'}
                label={mode === 'ai_vs_ai' ? `P2 · ${p2Label}` : 'AI Reasoning'}
              />
            </div>
          )}

          <div className="flex flex-col gap-2 pt-2 border-t border-cyber-border">
            <button
              onClick={() => setShowReasoning(v => !v)}
              className={`cyber-btn text-xs ${showReasoning ? 'bg-cyber-cyan/10' : ''}`}
            >
              {showReasoning ? 'Hide' : 'Show'} Reasoning
            </button>

            {/* Forfeit — only during active human battle */}
            {game.state.phase === 'battle' && mode === 'human_vs_ai' && (
              confirmForfeit ? (
                <div className="flex flex-col gap-1.5">
                  <div className="hud-label text-center text-cyber-orange">Concede defeat?</div>
                  <div className="flex gap-1.5">
                    <button onClick={handleForfeit} className="cyber-btn-danger flex-1 text-xs py-1">
                      Forfeit
                    </button>
                    <button onClick={() => setConfirmForfeit(false)} className="cyber-btn flex-1 text-xs py-1">
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button onClick={() => setConfirmForfeit(true)} className="cyber-btn text-xs">
                  Forfeit
                </button>
              )
            )}

            <button onClick={handleReset} className="cyber-btn text-xs">
              Main Menu
            </button>
          </div>

          {game.error && (
            <div className="px-2 py-1 border border-cyber-red text-cyber-red text-[10px]">
              {game.error}
            </div>
          )}
        </div>
      </div>

      {/* Game-over overlay */}
      {game.state.phase === 'game_over' && (
        <GameOverOverlay
          winner={game.state.winner}
          mode={mode}
          totalTurns={game.state.turn_number}
          onNewGame={handleReset}
        />
      )}
    </div>
  )
}

function GameOverOverlay({ winner, mode, totalTurns, onNewGame }: {
  winner: string | null
  mode: 'human_vs_ai' | 'ai_vs_ai'
  totalTurns: number
  onNewGame: () => void
}) {
  const isVictory = winner === 'player1' && mode === 'human_vs_ai'
  const winnerLabel = mode === 'ai_vs_ai'
    ? (winner === 'player1' ? 'Player 1' : 'Player 2') + ' wins'
    : winner === 'player1' ? 'You win' : 'You lose'

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-cyber-bg/80 backdrop-blur-sm z-50">
      <div className="cyber-panel p-10 flex flex-col items-center gap-6 text-center max-w-sm">
        <div className="text-5xl font-bold animate-flicker"
          style={{ textShadow: isVictory
            ? '0 0 20px rgba(0,255,180,0.8)'
            : '0 0 20px rgba(255,51,51,0.8)' }}>
          {isVictory ? '⚡ VICTORY' : '💀 DEFEAT'}
        </div>
        <div className="hud-value text-lg">{winnerLabel}</div>
        <div className="hud-label">{totalTurns} shots fired</div>
        <button onClick={onNewGame} className="cyber-btn px-8 py-3 text-sm mt-2">
          Main Menu
        </button>
      </div>
    </div>
  )
}
