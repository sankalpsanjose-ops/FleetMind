# FleetMind — Battleship Game Design Spec
**Date:** 2026-05-09  
**Status:** Approved for implementation

---

## Context

FleetMind is a feature-rich Battleship game built to showcase and compare AI model intelligence. The core experience is watching or playing against different LLMs (OpenAI, Anthropic Claude) playing Battleship — either with pure reasoning or augmented by a machine learning engine. The game emphasizes engine quality, AI decision-making, and gameplay depth over visual polish.

---

## Platform & Stack

- **Frontend:** React + TypeScript, PixiJS for game board canvas (swappable to Phaser later — board rendering is isolated behind a `GameBoard` component interface), Framer Motion for UI animations, TailwindCSS for HUD styling
- **Backend:** Python FastAPI — game logic, AI API calls, ML engine, all in one service
- **Database:** SQLite via SQLAlchemy — match history, scores, shot logs, fleet placement history
- **Communication:** REST for turn actions, WebSocket for real-time game events (AI vs AI spectator mode)
- **Visual style:** Sci-fi holographic — neon cyan/green on black, HUD-style UI, glowing grid, particle effects, all generated programmatically (no external image assets at launch)

---

## Game Modes

### Player Configurations
- **Human vs AI** — player places fleet, plays against an AI opponent
- **AI vs AI** — two AI opponents play autonomously; player watches in spectator mode

### Board Sizes
| Size | Grid | Notes |
|------|------|-------|
| Standard | 10×10 | Default |
| Large | 15×15 | Expanded fleet |
| Massive | 20×20 | Full armada |

### Difficulty Modes
Coverage % (~17% baseline) maintained proportionally across all board sizes by scaling fleet count.

Difficulty controls three things independently: fleet composition, ML layer intensity, and special rules. The AI provider (OpenAI/Claude) and AI mode (Pure/ML) are separate user selections — difficulty modulates how much strategic assistance the ML layer provides to that choice.

| Mode | Coverage | Fleet Composition | ML Layer Intensity | Special Rules |
|------|----------|-------------------|--------------------|---------------|
| 🟢 Cadet | 22% | Large ships only (Carrier×2, Battleship×2, Cruiser) | None — LLM instructed to play casually via system prompt | — |
| 🔵 Commander | 17% | Standard fleet (Carrier, Battleship, Cruiser, Sub, Patrol) | Heatmap only — top candidates passed to LLM | — |
| 🟠 Admiral | 15% | Lean fleet, more small ships | Heatmap + parity filter, weighted candidates (heatmap 0.8 / RL 0.2) | One radar ping per game (reveals 2×2 zone) |
| 🔴 War Veteran | 13% | Submarine swarm (no Carrier, many size-2/3 ships) | Full heatmap + RL (heatmap 0.6 / RL 0.4) + historical placement bias | AI learns from your past placements across sessions |
| ☠️ Black Ops | 10% | Ghost fleet (all ships size 2–3) | Full heatmap + RL (heatmap 0.3 / RL 0.7) | Human player only sees last 5 moves on attack grid. In AI vs AI mode, fog applies to neither AI (it's a visual-only constraint). |
| ⚔️ Armada | 20% | 2× standard fleet | Heatmap only (heatmap 0.8 / RL 0.2) | Best on 15×15 or 20×20; ideal for AI vs AI |
| 🎯 Guerrilla | 17% | Asymmetric — human (or AI player 1) gets 1 Carrier; AI (or AI player 2) gets 8 small ships. Equal total cells. | Heatmap only | In AI vs AI mode, Player 1 always gets the Carrier side. Completely different hunt strategy required each side. |

---

## Game Engine

Single source of truth. All rules enforced here. UI is read-only against engine state.

### State Machine
```
SETUP → PLACEMENT → BATTLE → GAME_OVER
```

- **SETUP:** Board size, difficulty mode, opponent configuration selected
- **PLACEMENT:** Fleets placed. Human via drag-and-drop UI. AI via strategic dispersion algorithm. Fleet positions **sealed** after this phase — never exposed to AI layer again.
- **BATTLE:** Turns alternate. Engine validates shots (no repeats, in-bounds). Emits events over WebSocket: `shot_fired`, `ship_sunk`, `game_over`.
- **GAME_OVER:** All ships of one side sunk. Result recorded to DB.

### Anti-Cheat Enforcement (Architectural)
Two separate, non-referencing data models:
- `fleet_state` — ship positions. **Never serialized or passed to AI layer.**
- `attack_state` — hits/misses/unknown per cell. **Only data the AI ever receives.**

`MoveRequestBuilder` accepts only `attack_state`. It cannot access `fleet_state` by construction.

### Ship Validation
- No overlapping ships
- No out-of-bounds placement
- Configurable minimum gap between ships per difficulty (Cadet: 0, Admiral+: 1 cell gap enforced)

### Fleet Configuration by Board Size
Ships scale proportionally to maintain coverage ratio. Example for Commander (17%):

| Board | Ships | Occupied Cells | Coverage |
|-------|-------|----------------|----------|
| 10×10 | Carrier(5), Battleship(4), Cruiser(3), Sub(3), Patrol(2) | 17 | 17% |
| 15×15 | Above + Destroyer(4), Frigate(3), Speedboat(2) | ~38 | ~17% |
| 20×20 | Above + 2×Carrier, 2×Battleship, Corvette(2) | ~68 | ~17% |

---

## AI Layer

### Provider Abstraction
```python
class AIProvider(ABC):
    async def decide_move(self, attack_grid: Grid, game_context: GameContext) -> MoveDecision:
        ...

class OpenAIProvider(AIProvider): ...
class AnthropicProvider(AIProvider): ...
# Future: GeminiProvider, GrokProvider, MistralProvider, etc.
```

`GameContext` contains: board size, difficulty mode, remaining ship counts/sizes, turn number, optional reasoning flag. **Never fleet positions.**

### Pure AI Mode
- LLM receives structured attack grid + game context
- System prompt activates the model's own knowledge of probability theory, parity targeting, and game strategy — no pre-loaded RAG; the model reasons from its own training
- Returns: coordinate + optional reasoning text (displayed if player toggled reasoning panel on)

### AI + ML Mode
```
Board State → Probability Engine → Top-5 candidates
                                        ↓
                              LLM receives candidates + board context
                                        ↓
                              LLM reasons, selects final coordinate
```

Combined scoring: `heatmap_score × 0.6 + rl_qvalue_normalized × 0.4`  
Weights shift by difficulty (Black Ops: 0.3/0.7, more RL aggression).

### AI Reasoning Display
Optional panel toggled per match. When enabled, AI's reasoning text is shown in a HUD panel during its turn. When disabled, only the move result is shown.

---

## ML Engine

Pluggable strategy interface — same philosophy as AI provider abstraction. New strategies (Monte Carlo Bayesian, DQN) slot in without touching game engine.

### Component 1 — Probability Heatmap (Commander and above)
- Maintains probability score for every unknown cell
- After miss: eliminates cells where no remaining ship fits
- After hit: concentrates probability along hit axis
- Parity filtering: ignores cells unreachable by smallest remaining ship
- Recomputes every turn, O(board × ships)

### Component 2 — Q-Learning RL Agent (AI+ML mode)
- **State:** encoded attack grid + remaining ship sizes
- **Reward:** +1 hit, +5 ship sunk, +20 game won, −0.1 per miss
- Trains asynchronously after each completed game (non-blocking)
- War Veteran mode: secondary bias layer cross-references personal placement history from DB, upweights historically favored cells
- Model checkpoint saved to disk, loaded on server start

### v2 Upgrade Path (pluggable, no engine changes needed)
- **Monte Carlo Bayesian Inference** — simulate thousands of valid fleet arrangements, pick highest-probability cell. Strongest single upgrade.
- **Deep Q-Network (DQN)** — neural net Q-function, handles 15×15 and 20×20 boards better than tabular Q-learning
- **PPO / Policy Gradient** — more stable long-term RL training

---

## Match Management & Persistence

### SQLite Schema
```sql
matches
  id, board_size, difficulty_mode,
  player_type (human|ai),
  ai_provider_1, ai_mode_1 (pure|ml),
  ai_provider_2, ai_mode_2,
  winner, total_turns, duration_seconds, created_at

shots
  id, match_id, turn_number, side (player1|player2),
  coordinate, result (hit|miss|sunk), ship_type_sunk,
  reasoning_text, timestamp

placements  -- anonymized, used for War Veteran bias learning
  id, match_id, side, ship_type, orientation, start_coordinate
```

### Match History Features
- Win/loss record per AI model and per difficulty
- "Claude vs GPT-4o: 23 matches, Claude wins 61%" leaderboard
- Reasoning replay (if captured, stored with shots)
- War Veteran bias learning reads `placements` table
- RL training reads `shots` + match outcome

---

## Project Structure
```
FleetMind/
├── frontend/                  # React + TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── GameBoard/     # PixiJS canvas — isolated, swappable
│   │   │   ├── HUD/           # Sci-fi overlay, reasoning panel
│   │   │   ├── Setup/         # Mode selection, fleet placement
│   │   │   └── MatchHistory/  # Leaderboard, stats
│   │   ├── hooks/             # Game state, WebSocket
│   │   └── types/
├── backend/                   # Python FastAPI
│   ├── game/
│   │   ├── engine.py          # State machine, rules, anti-cheat
│   │   ├── fleet.py           # Ship models, placement validation
│   │   └── events.py          # WebSocket event emitter
│   ├── ai/
│   │   ├── provider.py        # AIProvider ABC
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── move_request.py    # MoveRequestBuilder (attack_state only)
│   ├── ml/
│   │   ├── strategy.py        # MLStrategy ABC — pluggable
│   │   ├── heatmap.py         # Probability heatmap
│   │   ├── qlearning.py       # Q-learning RL agent
│   │   └── trainer.py         # Async post-game training loop
│   ├── db/
│   │   ├── models.py          # SQLAlchemy models
│   │   └── repository.py      # Match/shot/placement persistence
│   └── main.py                # FastAPI app, routes, WebSocket
└── docs/
    └── superpowers/specs/
        └── 2026-05-09-fleetmind-battleship-design.md
```

---

## Verification Plan

1. **Game Engine:** Unit test every rule — overlapping placement rejected, repeat shots rejected, win condition triggers correctly, fleet_state never leaks into attack_state
2. **AI Layer:** Mock provider returns valid coordinates only. Test that MoveRequestBuilder never includes fleet positions in any serialized output.
3. **ML Heatmap:** After known hits/misses, verify probability scores concentrate correctly. Verify parity filtering eliminates unreachable cells.
4. **RL Training:** Simulate 100 games, verify Q-values converge, verify training runs async without blocking game turns
5. **Anti-cheat:** Integration test — complete a full game, assert `placements` data is never present in any AI API call payload
6. **Match Persistence:** Full game → verify match, shots, and placements all written correctly → start new game in War Veteran mode → verify bias layer loads from placements table
7. **WebSocket:** AI vs AI game → verify frontend receives all events in order with no dropped frames
8. **Difficulty scaling:** Verify coverage % lands within ±1% of target for all 7 modes × 3 board sizes
