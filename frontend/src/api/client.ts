import axios from 'axios'
import type { GameState, MatchRecord, WinRates, ShipPlacement, BoardSize, Difficulty, AIMode, AIProvider } from '../types/game'

const api = axios.create({ baseURL: '/' })

export interface CreateGameParams {
  board_size: BoardSize
  difficulty: Difficulty
  player1_type: 'human' | 'ai'
  player2_type: 'human' | 'ai'
  ai_provider_1?: AIProvider
  ai_mode_1?: AIMode
  ai_provider_2?: AIProvider
  ai_mode_2?: AIMode
  show_reasoning?: boolean
}

export interface CreateGameResponse {
  game_id: string
  phase: string
  board_size: number
}

export interface FireResponse {
  result: 'hit' | 'miss' | 'sunk'
  ship_type: string | null
  reasoning: string | null
  game_over: boolean
  winner: string | null
}

export const gameApi = {
  create: (params: CreateGameParams) =>
    api.post<CreateGameResponse>('/games', params).then(r => r.data),

  placeFleet: (gameId: string, ships: ShipPlacement[]) =>
    api.post<{ success: boolean }>(`/games/${gameId}/placement`, { ships }).then(r => r.data),

  fire: (gameId: string, row: number, col: number) =>
    api.post<FireResponse>(`/games/${gameId}/fire`, { row, col }).then(r => r.data),

  getState: (gameId: string) =>
    api.get<GameState>(`/games/${gameId}/state`).then(r => r.data),
}

export const matchApi = {
  list: () =>
    api.get<MatchRecord[]>('/matches').then(r => r.data),

  winRates: () =>
    api.get<WinRates>('/matches/win-rates').then(r => r.data),
}
