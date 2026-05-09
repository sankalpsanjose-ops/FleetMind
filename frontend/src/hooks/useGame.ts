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

function mergeGrid(prev: AttackGrid, side: 'player1' | 'player2', row: number, col: number, result: CellState): AttackGrid {
  const key = `${row},${col}`
  return { ...prev, [side]: { ...prev[side], [key]: result } }
}

export function useGame() {
  const [store, setStore] = useState<GameStore>(EMPTY)

  const handleEvent = useCallback((event: WSEvent) => {
    setStore(prev => {
      switch (event.type) {
        case 'connected':
          return {
            ...prev,
            error: null,
            state: {
              game_id: event.game_id,
              phase: event.phase,
              current_turn: 'player1',
              turn_number: 0,
              winner: null,
              attack_grid: prev.state?.attack_grid ?? { player1: {}, player2: {} },
            },
          }

        case 'ai_thinking':
          return { ...prev, isAiThinking: true }

        case 'shot_fired': {
          const side = event.side as 'player1' | 'player2'
          const turnNum = event.turn_number ?? prev._turnCounter + 1
          const entry: GameLog = {
            turn: turnNum,
            side,
            row: event.row,
            col: event.col,
            result: event.result,
            shipType: event.ship_type,
            reasoning: event.reasoning,
          }
          const grid = prev.state?.attack_grid ?? { player1: {}, player2: {} }
          return {
            ...prev,
            isAiThinking: false,
            _turnCounter: turnNum,
            log: [...prev.log, entry],
            state: prev.state
              ? { ...prev.state, attack_grid: mergeGrid(grid, side, event.row, event.col, event.result) }
              : prev.state,
          }
        }

        case 'ship_sunk':
          // Visual feedback handled via shot_fired result='sunk'; no extra state needed
          return prev

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
            state: prev.state
              ? { ...prev.state, phase: 'game_over', winner: event.winner, turn_number: event.total_turns }
              : prev.state,
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

  const placeFleet = useCallback(async (ships: Parameters<typeof gameApi.placeFleet>[1]) => {
    if (!store.gameId) return
    const res = await gameApi.placeFleet(store.gameId, ships)
    // Update phase from REST response (WS state event follows)
    if ('phase' in res) {
      setStore(prev => prev.state ? { ...prev, state: { ...prev.state!, phase: (res as any).phase } } : prev)
    }
  }, [store.gameId])

  const humanFire = useCallback(async (row: number, col: number) => {
    if (!store.gameId) return
    try {
      await gameApi.fire(store.gameId, row, col)
    } catch (err: any) {
      setStore(prev => ({ ...prev, error: err?.response?.data?.detail ?? String(err) }))
    }
  }, [store.gameId])

  const startAiVsAi = useCallback(() => {
    send({ action: 'start_ai_vs_ai' })
  }, [send])

  const requestState = useCallback(() => {
    send({ action: 'get_state' })
  }, [send])

  // Expose without internal _turnCounter
  const { _turnCounter: _tc, ...publicStore } = store
  return {
    ...publicStore,
    createGame,
    placeFleet,
    humanFire,
    startAiVsAi,
    requestState,
  }
}
