from __future__ import annotations
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from backend.api.orchestrator import get_orchestrator, GameOrchestrator
from backend.game.models import GamePhase

async def game_ws_endpoint(websocket: WebSocket, game_id: str):
    """
    WebSocket endpoint for live game events.

    Client connects: ws://host/ws/games/{game_id}
    Server pushes: shot_fired, ship_sunk, ai_thinking, game_over events as JSON.
    Client can send: {"action": "start_ai_vs_ai"} to kick off AI vs AI loop.
    """
    await websocket.accept()
    orchestrator = get_orchestrator()

    try:
        session = orchestrator.get_session(game_id)
    except KeyError:
        await websocket.send_json({"type": "error", "message": "Game not found"})
        await websocket.close()
        return

    # Register this WebSocket as an event listener
    async def send_event(event: dict) -> None:
        try:
            await websocket.send_json(event)
        except Exception:
            pass

    session.register_event_callback(send_event)

    # Send current state immediately on connect
    await websocket.send_json({
        "type": "connected",
        "game_id": game_id,
        "phase": session.engine.state.phase.value,
        "board_size": session.board_size.value,
        "difficulty": session.difficulty.value,
    })

    # Auto-start AI vs AI without waiting for client message — the client sends
    # start_ai_vs_ai before the WS handshake completes, so the message is dropped.
    if (session.player1.player_type == "ai"
            and session.player2.player_type == "ai"
            and session.engine.state.phase == GamePhase.BATTLE):
        asyncio.create_task(orchestrator.run_ai_vs_ai(game_id))

    try:
        while True:
            # Wait for client messages
            data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
            msg = json.loads(data)

            action = msg.get("action")

            if action == "start_ai_vs_ai":
                if session.engine.state.phase != GamePhase.BATTLE:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Game not in battle phase"
                    })
                    continue
                # Run AI vs AI loop in background so WebSocket stays responsive
                asyncio.create_task(orchestrator.run_ai_vs_ai(game_id))

            elif action == "get_state":
                state = orchestrator.get_state(game_id)
                await websocket.send_json({"type": "state", **state})

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except asyncio.TimeoutError:
        await websocket.close(code=1001)
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
