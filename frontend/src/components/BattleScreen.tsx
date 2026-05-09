import { useState, useCallback } from 'react'
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
  const [setupParams, setSetupParams] = useState<CreateGameParams | null>(null)
  const [starting, setStarting] = useState(false)
  const [showReasoning, setShowReasoning] = useState(false)
  const [boardSizeNum, setBoardSizeNum] = useState(10)
  const [difficulty, setDifficulty] = useState('commander')
  const [mode, setMode] = useState<'human_vs_ai' | 'ai_vs_ai'>('human_vs_ai')

  const isHumanTurn = game.state?.phase === 'battle' &&
    game.state.current_turn === 'player1' &&
    mode === 'human_vs_ai'

  const handleModeStart = useCallback(async (params: CreateGameParams) => {
    setStarting(true)
    setSetupParams(params)
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
    // Ask server to assign random placement
    await gameApi.placeFleet(game.gameId, [])  // empty = server-side random
  }, [game.gameId])

  const handleCellClick = useCallback((row: number, col: number) => {
    if (!isHumanTurn) return
    game.humanFire(row, col)
  }, [isHumanTurn, game])

  const handleStartAiVsAi = useCallback(() => {
    game.startAiVsAi()
  }, [game])

  const handleReset = () => {
    setSetupParams(null)
    window.location.reload()
  }

  // ── No game yet: show mode selector
  if (!game.gameId || !game.state) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-8">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-shadow-cyan mb-1 animate-flicker">FLEET<span className="text-cyber-blue">MIND</span></h1>
          <div className="hud-label tracking-[0.5em]">AI Battleship</div>
        </div>
        <ModeSelector onStart={handleModeStart} loading={starting} />
      </div>
    )
  }

  // ── Human placement phase
  if (game.state.phase === 'placement' && mode === 'human_vs_ai') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-8">
        <FleetPlacement
          boardSize={boardSizeNum}
          onConfirm={handlePlacementConfirm}
          onRandomize={handleRandomize}
        />
      </div>
    )
  }

  // ── Battle / Game Over / AI-vs-AI setup
  return (
    <div className="flex flex-col h-screen overflow-hidden">
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
              label="[ P1 — Your Shots ]"
              onCellClick={handleCellClick}
              interactive={isHumanTurn}
            />
          </div>
          <div className="flex-1 max-w-[480px]">
            <GameBoard
              boardSize={boardSizeNum}
              attackGrid={game.state.attack_grid.player2}
              side="player2"
              label="[ P2 — Enemy Shots ]"
            />
          </div>
        </div>

        {/* Right panel */}
        <div className="flex flex-col w-64 border-l border-cyber-border p-3 gap-3 overflow-hidden">
          <ShotLog log={game.log} />

          {showReasoning && (
            <div className="flex-1 overflow-hidden">
              <ReasoningPanel log={game.log} show={showReasoning} />
            </div>
          )}

          {/* Controls */}
          <div className="flex flex-col gap-2 pt-2 border-t border-cyber-border">
            <button
              onClick={() => setShowReasoning(v => !v)}
              className={`cyber-btn text-xs ${showReasoning ? 'bg-cyber-cyan/10' : ''}`}
            >
              {showReasoning ? 'Hide' : 'Show'} Reasoning
            </button>

            {mode === 'ai_vs_ai' && game.state.phase === 'placement' && (
              <button onClick={handleStartAiVsAi} className="cyber-btn text-xs">
                Start Battle
              </button>
            )}

            {game.state.phase === 'game_over' && (
              <button onClick={handleReset} className="cyber-btn text-xs">
                New Game
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
