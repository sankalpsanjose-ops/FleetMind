import { useEffect, useRef } from 'react'
import type { GameLog } from '../../hooks/useGame'

interface Props {
  log: GameLog[]
  show: boolean
  side?: 'player1' | 'player2' | 'all'  // default 'all'
  label?: string
}

export function ReasoningPanel({ log, show, side = 'all', label = 'AI Reasoning' }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [log])

  if (!show) return null

  const entries = log.filter(e =>
    e.reasoning && (side === 'all' || e.side === side)
  )

  return (
    <div className="cyber-panel flex flex-col h-full overflow-hidden">
      <div className="hud-label px-3 py-2 border-b border-cyber-border shrink-0">{label}</div>
      <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-3">
        {entries.length === 0 && (
          <div className="text-cyber-dim text-[10px] italic px-1 pt-1">Awaiting moves…</div>
        )}
        {entries.map((entry, i) => (
          <div key={i} className="text-[10px] leading-relaxed">
            <div className="flex gap-2 mb-0.5 items-center">
              <span className={`hud-label text-[9px] ${entry.side === 'player1' ? 'text-cyber-cyan' : 'text-cyber-blue'}`}>
                {entry.side === 'player1' ? 'P1' : 'P2'}
              </span>
              <span className="hud-label text-[9px]">T{entry.turn}</span>
              <span className={`uppercase text-[9px] ${
                entry.result === 'sunk' ? 'text-cyber-orange' :
                entry.result === 'hit'  ? 'text-cyber-red' :
                'text-cyber-dim'
              }`}>{entry.result}</span>
              <span className="text-cyber-dim text-[9px]">({entry.row},{entry.col})</span>
            </div>
            <div className="text-cyber-dim border-l-2 border-cyber-border pl-2 leading-snug">
              {entry.reasoning}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
