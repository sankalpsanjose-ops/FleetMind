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

    // In prod: derive wss:// from VITE_API_URL (https://... → wss://...)
    // In dev: fall back to same-host (Vite proxy handles /ws)
    const apiUrl = import.meta.env.VITE_API_URL as string | undefined
    const wsBase = apiUrl
      ? apiUrl.replace(/^http/, 'ws')
      : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
    const ws = new WebSocket(`${wsBase}/ws/games/${gameId}`)
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
