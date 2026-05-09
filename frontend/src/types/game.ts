export type CellState = 'unknown' | 'miss' | 'hit' | 'sunk'
export type GamePhase = 'setup' | 'placement' | 'battle' | 'game_over'
export type Orientation = 'horizontal' | 'vertical'
export type PlayerType = 'human' | 'ai'
export type AIMode = 'pure' | 'ml'
export type AIProvider = 'openai' | 'anthropic'
export type BoardSize = 'standard' | 'large' | 'massive'
export type Difficulty =
  | 'cadet' | 'commander' | 'admiral'
  | 'war_veteran' | 'black_ops' | 'armada' | 'guerrilla'

export interface Coordinate { row: number; col: number }

export interface ShipPlacement {
  ship_type: string
  orientation: Orientation
  row: number
  col: number
}

export interface AttackGrid {
  player1: Record<string, CellState>   // "row,col" -> state
  player2: Record<string, CellState>
}

export interface GameState {
  game_id: string
  phase: GamePhase
  current_turn: 'player1' | 'player2'
  turn_number: number
  winner: string | null
  attack_grid: AttackGrid
}

// WebSocket events from server
export type WSEvent =
  | { type: 'connected'; game_id: string; phase: GamePhase; board_size: number; difficulty: string }
  | { type: 'ai_thinking'; side: string; turn: number }
  | { type: 'shot_fired'; side: string; row: number; col: number; result: CellState; ship_type: string | null; reasoning: string | null; turn_number?: number }
  | { type: 'ship_sunk'; side: string; ship_type: string }
  | { type: 'game_over'; winner: string; total_turns: number }
  | { type: 'state'; phase: GamePhase; current_turn: string; turn_number: number; winner: string | null; attack_grid: AttackGrid }
  | { type: 'error'; message: string }
  | { type: 'pong' }

export interface MatchRecord {
  id: number
  board_size: number
  difficulty: string
  ai_provider_1: string | null
  ai_provider_2: string | null
  winner: string | null
  total_turns: number | null
  created_at: string
}

export interface WinRates {
  [provider: string]: { wins: number; losses: number; total: number }
}
