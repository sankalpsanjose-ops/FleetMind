from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.db.database import engine, Base
from backend.api.routes import router
from backend.api.websocket import game_ws_endpoint

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FleetMind", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.websocket("/ws/games/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await game_ws_endpoint(websocket, game_id)

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}
