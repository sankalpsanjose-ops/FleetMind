from backend.game.models import DifficultyMode

# For models with extended thinking — minimal guardrails, let it reason freely.
# The soft nudge about active hits is still useful: even 10k thinking tokens can
# miss obvious follow-ups when the board is noisy with many misses.
_FORMAT_THINKING = """
Note: if active hits (unsunk) are present, strongly consider firing adjacent to them.

Respond in EXACTLY this format (two lines):
REASON: <one sentence summarising your conclusion>
FIRE: <row,col>"""

# For single-pass models — a priority nudge so they don't ignore active hits.
_FORMAT_STANDARD = """
Priority: if active hits (unsunk) exist, fire adjacent to one of them before hunting elsewhere.

Respond in EXACTLY this format (two lines):
REASON: <one tactical sentence explaining your choice>
FIRE: <row,col>"""

SYSTEM_PROMPTS: dict[DifficultyMode, str] = {
    DifficultyMode.CADET: (
        "You are playing Battleship casually. Make reasonable but suboptimal choices. "
        "Avoid complex probability — just pick cells that seem okay."
    ),

    DifficultyMode.COMMANDER: (
        "You are playing Battleship with the hunt-and-target strategy.\n"
        "Hunt mode (no active hits): spread shots across the board.\n"
        "Target mode (active hits): fire adjacent to hit cells to find the axis, then follow it to sink the ship."
    ),

    DifficultyMode.ADMIRAL: (
        "You are playing Battleship as an Admiral. Use advanced strategy:\n"
        "1. Parity: skip cells no remaining ship can reach.\n"
        "2. Hunt mode: prefer cells that maximise valid ship placements.\n"
        "3. Target mode: lock onto the confirmed hit axis and follow it until the ship is sunk.\n"
        "ML candidates show the top-probability cells — follow or override with justification."
    ),

    DifficultyMode.WAR_VETERAN: (
        "You are a battle-hardened Battleship veteran.\n"
        "1. Probability density — count valid placements per cell for each remaining ship size.\n"
        "2. Strict parity filtering — eliminate cells no ship can reach.\n"
        "3. Hit axis locking — never deviate from a partially-sunk ship until fully sunk.\n"
        "4. Exploit tendencies: ships rarely in corners, prefer horizontal, avoid adjacency.\n"
        "ML candidates are statistically optimal — treat them as strong signals."
    ),

    DifficultyMode.BLACK_OPS: (
        "You are a ghost operative in Battleship blackout conditions. Apply everything:\n"
        "1. Maximum probability density — fire where ship placements converge.\n"
        "2. Parity and constraint propagation after every shot.\n"
        "3. Aggressive axis locking — never deviate from a partially-sunk ship.\n"
        "4. Exploit any behavioural patterns visible in the shot history.\n"
        "ML candidates are your intelligence — weight them heavily. Be ruthless."
    ),

    DifficultyMode.ARMADA: (
        "You are commanding a large fleet engagement. Apply probability-based targeting, "
        "hit axis exploitation, and systematic board coverage. Finish each partially-sunk "
        "ship before moving on. ML candidates show the highest-probability targets."
    ),

    DifficultyMode.GUERRILLA: (
        "You are playing asymmetric Battleship. Adapt your strategy:\n"
        "- Hunting a large ship (Carrier): concentrate fire centrally with long scan lines.\n"
        "- Hunting many small ships: apply strict parity — they hide in any corner.\n"
        "Use probability reasoning for the asymmetric fleet composition."
    ),
}

def get_system_prompt(difficulty: DifficultyMode, thinking: bool = False) -> str:
    base = SYSTEM_PROMPTS[difficulty]
    fmt  = _FORMAT_THINKING if thinking else _FORMAT_STANDARD
    return base + "\n" + fmt

def build_user_message(prompt_ctx: dict) -> str:
    lines = [
        f"Board size: {prompt_ctx['board_size']}x{prompt_ctx['board_size']}",
        f"Turn: {prompt_ctx['turn_number']}",
        f"Remaining enemy ships (sizes): {prompt_ctx['remaining_ship_sizes']}",
        f"Your hits so far: {prompt_ctx['hit_count']} | Cells remaining: {prompt_ctx['unknown_count']}",
        f"Active hits (unsunk): {prompt_ctx['hit_coordinates'] or 'none'}",
        "",
        "Attack grid (· = unknown, ○ = miss, X = hit, # = sunk):",
        prompt_ctx["grid_text"],
    ]
    if "ml_candidates" in prompt_ctx:
        lines += ["", f"Top ML candidates (highest probability): {prompt_ctx['ml_candidates']}"]
    return "\n".join(lines)
