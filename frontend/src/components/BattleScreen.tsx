import { useState, useCallback, useEffect, useRef } from 'react'
import { useGame } from '../hooks/useGame'
import { gameApi, type CreateGameParams } from '../api/client'
import { GameBoard } from './GameBoard/GameBoard'
import { StatusBar } from './HUD/StatusBar'
import { ShotLog } from './HUD/ShotLog'
import { ReasoningPanel } from './HUD/ReasoningPanel'
import { ModeSelector } from './Setup/ModeSelector'
import { FleetPlacement } from './Setup/FleetPlacement'
import type { ShipPlacement } from '../types/game'

const BOARD_SIZE_MAP = { standard: 10, large: 15, massive: 20 }

export function BattleScreen() {
  const game = useGame()
  const [starting, setStarting] = useState(false)
  const [showReasoning, setShowReasoning] = useState(false)
  const [boardSizeNum, setBoardSizeNum] = useState(10)
  const [difficulty, setDifficulty] = useState('commander')
  const [mode, setMode] = useState<'human_vs_ai' | 'ai_vs_ai'>('human_vs_ai')
  const aiStartedRef = useRef(false)

  const isHumanTurn = game.state?.phase === 'battle' &&
    game.state.current_turn === 'player1' &&
    mode === 'human_vs_ai'

  // Auto-trigger AI vs AI battle when WS connects into battle phase
  useEffect(() => {
    if (mode === 'ai_vs_ai' && game.state?.phase === 'battle' && !aiStartedRef.current) {
      aiStartedRef.current = true
      game.startAiVsAi()
    }
  }, [mode, game.state?.phase]) // eslint-disable-line

  const handleModeStart = useCallback(async (params: CreateGameParams) => {
    setStarting(true)
    aiStartedRef.current = false
    setBoardSizeNum(BOARD_SIZE_MAP[params.board_size])
    setDifficulty(params.difficulty)
    setMode(params.player1_type === 'human' ? 'human_vs_ai' : 'ai_vs_ai')
    setShowReasoning(params.show_reasoning ?? false)
    try {
      await game.createGame(params)
    } finally {
      setStarting(false)
    }
  }, [game])

  const handlePlacementConfirm = useCallback(async (placements: ShipPlacement[]) => {
    await game.placeFleet(placements)
  }, [game])

  const handleRandomize = useCallback(async () => {
    if (!game.gameId) return
    await gameApi.placeFleet(game.gameId, [])  // empty = server-side random
  }, [game.gameId])

  const handleCellClick = useCallback((row: number, col: number) => {
    if (!isHumanTurn) return
    game.humanFire(row, col)
  }, [isHumanTurn, game])

  const handleReset = () => {
    aiStartedRef.current = false
    window.location.reload()
  }

  // ── No game yet: show mode selector
  if (!game.gameId || !game.state) {
    return (
      <div className="flex flex-col items-center justify-center min-h-full p-8 bg-cyber-bg">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-shadow-cyan mb-2 animate-flicker">
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
    )
  }

  // ── Human placement phase
  if (game.state.phase === 'placement' && mode === 'human_vs_ai') {
    return (
      <div className="flex flex-col items-center justify-center min-h-full p-8 bg-cyber-bg">
        <FleetPlacement
          boardSize={boardSizeNum}
          onConfirm={handlePlacementConfirm}
          onRandomize={handleRandomize}
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
        {/* Boards */}
        <div className="flex flex-1 items-center justify-center gap-6 p-4">
          <div className="flex-1 max-w-[480px]">
            <GameBoard
              boardSize={boardSizeNum}
              attackGrid={game.state.attack_grid.player1}
              side="player1"
              label={mode === 'human_vs_ai' ? '[ YOUR SHOTS ]' : '[ P1 — SHOTS ]'}
              onCellClick={handleCellClick}
              interactive={isHumanTurn}
            />
          </div>
          <div className="flex-1 max-w-[480px]">
            <GameBoard
              boardSize={boardSizeNum}
              attackGrid={game.state.attack_grid.player2}
              side="player2"
              label={mode === 'human_vs_ai' ? '[ ENEMY SHOTS ]' : '[ P2 — SHOTS ]'}
            />
          </div>
        </div>

        {/* Right sidebar */}
        <div className="flex flex-col w-64 border-l border-cyber-border p-3 gap-3 overflow-hidden shrink-0">
          <ShotLog log={game.log} />

          {showReasoning && (
            <div className="flex-1 min-h-0">
              <ReasoningPanel log={game.log} show={showReasoning} />
            </div>
          )}

          <div className="flex flex-col gap-2 pt-2 border-t border-cyber-border">
            <button
              onClick={() => setShowReasoning(v => !v)}
              className={`cyber-btn text-xs ${showReasoning ? 'bg-cyber-cyan/10' : ''}`}
            >
              {showReasoning ? 'Hide' : 'Show'} Reasoning
            </button>

            {game.state.phase === 'game_over' && (
              <button onClick={handleReset} className="cyber-btn text-xs">
                New Game
              </button>
            )}
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
          totalTurns={game.state.turn_number}
          onNewGame={handleReset}
        />
      )}
    </div>
  )
}

function GameOverOverlay({ winner, totalTurns, onNewGame }: {
  winner: string | null
  totalTurns: number
  onNewGame: () => void
}) {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-cyber-bg/80 backdrop-blur-sm z-50">
      <div className="cyber-panel p-10 flex flex-col items-center gap-6 text-center max-w-sm">
        <div className="text-5xl font-bold text-shadow-cyan animate-flicker">
          {winner === 'player1' ? '⚡ VICTORY' : '💀 DEFEAT'}
        </div>
        <div className="hud-value text-lg">
          {winner === 'player1' ? 'Player 1' : 'Player 2'} wins
        </div>
        <div className="hud-label">
          {totalTurns} total shots fired
        </div>
        <button onClick={onNewGame} className="cyber-btn px-8 py-3 text-sm mt-2">
          Deploy New Fleet
        </button>
      </div>
    </div>
  )
}
