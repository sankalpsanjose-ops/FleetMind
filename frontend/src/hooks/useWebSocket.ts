import { useEffect, useRef, useCallback } from 'react'
import type { WSEvent } from '../types/game'

type Handler = (event: WSEvent) => void

export function useWebSocket(gameId: string | null, onEvent: Handler) {
  const wsRef = useRef<WebSocket | null>(null)
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  const send = useCallback((msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  useEffect(() => {
    if (!gameId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/games/${gameId}`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as WSEvent
        onEventRef.current(event)
      } catch {
        // ignore malformed messages
      }
    }

    // keepalive ping every 25s
    const pingInterval = setInterval(() => send({ action: 'ping' }), 25_000)

    return () => {
      clearInterval(pingInterval)
      ws.close()
    }
  }, [gameId, send])

  return { send }
}
