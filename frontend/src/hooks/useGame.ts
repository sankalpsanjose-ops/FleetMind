import { useState, useCallback } from 'react'
import { gameApi, type CreateGameParams } from '../api/client'
import { useWebSocket } from './useWebSocket'
import type { GameState, WSEvent, CellState, AttackGrid } from '../types/game'

export interface GameLog {
  turn: number
  side: string
  row: number
  col: number
  result: CellState
  shipType: string | null
  reasoning: string | null
}

interface GameStore {
  gameId: string | null
  state: GameState | null
  log: GameLog[]
  isAiThinking: boolean
  error: string | null
  _turnCounter: number
}

const EMPTY: GameStore = {
  gameId: null,
  state: null,
  log: [],
  isAiThinking: false,
  error: null,
  _turnCounter: 0,
}

function mergeAttackGrid(prev: AttackGrid | undefined, side: string, row: number, col: number, result: CellState): AttackGrid {
  const base = prev ?? { player1: {}, player2: {} }
  const key = `${row},${col}`
  return {
    ...base,
    [side]: { ...base[side as 'player1' | 'player2'], [key]: result },
  }
}

export function useGame() {
  const [store, setStore] = useState<GameStore>(EMPTY)

  const handleEvent = useCallback((event: WSEvent) => {
    setStore(prev => {
      switch (event.type) {
        case 'connected':
          return {
            ...prev,
            state: {
              ...prev.state!,
              phase: event.phase,
              game_id: event.game_id,
              current_turn: 'player1',
              turn_number: 0,
              winner: null,
              attack_grid: { player1: {}, player2: {} },
            },
          }
        case 'ai_thinking':
          return { ...prev, isAiThinking: true }
        case 'shot_fired': {
          const cellState = event.result as CellState
          const side = event.side as 'player1' | 'player2'
          const turnNum = event.turn_number ?? prev._turnCounter + 1
          const newEntry: GameLog = {
            turn: turnNum,
            side,
            row: event.row,
            col: event.col,
            result: cellState,
            shipType: event.ship_type,
            reasoning: event.reasoning,
          }
          return {
            ...prev,
            isAiThinking: false,
            _turnCounter: turnNum,
            log: [...prev.log, newEntry],
            state: prev.state ? {
              ...prev.state,
              attack_grid: mergeAttackGrid(prev.state.attack_grid, side, event.row, event.col, cellState),
            } : prev.state,
          }
        }
        case 'state':
          return {
            ...prev,
            isAiThinking: false,
            state: prev.state ? {
              ...prev.state,
              phase: event.phase,
              current_turn: event.current_turn as 'player1' | 'player2',
              turn_number: event.turn_number,
              winner: event.winner,
              attack_grid: event.attack_grid,
            } : prev.state,
          }
        case 'game_over':
          return {
            ...prev,
            isAiThinking: false,
            state: prev.state ? { ...prev.state, phase: 'game_over', winner: event.winner } : prev.state,
          }
        case 'error':
          return { ...prev, error: event.message, isAiThinking: false }
        default:
          return prev
      }
    })
  }, [])

  const { send } = useWebSocket(store.gameId, handleEvent)

  const createGame = useCallback(async (params: CreateGameParams) => {
    setStore(EMPTY)
    const res = await gameApi.create(params)
    setStore(prev => ({
      ...prev,
      gameId: res.game_id,
      state: {
        game_id: res.game_id,
        phase: res.phase as GameState['phase'],
        current_turn: 'player1',
        turn_number: 0,
        winner: null,
        attack_grid: { player1: {}, player2: {} },
      },
    }))
    return res.game_id
  }, [])

  const placeFleet = useCallback(async (placements: Parameters<typeof gameApi.placeFleet>[1]) => {
    if (!store.gameId) return
    await gameApi.placeFleet(store.gameId, placements)
  }, [store.gameId])

  const humanFire = useCallback(async (row: number, col: number) => {
    if (!store.gameId) return
    await gameApi.fire(store.gameId, row, col)
  }, [store.gameId])

  const startAiVsAi = useCallback(() => {
    send({ action: 'start_ai_vs_ai' })
  }, [send])

  const requestState = useCallback(() => {
    send({ action: 'get_state' })
  }, [send])

  return {
    ...store,
    createGame,
    placeFleet,
    humanFire,
    startAiVsAi,
    requestState,
  }
}
