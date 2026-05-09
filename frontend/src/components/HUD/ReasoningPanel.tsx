import { useEffect, useRef } from 'react'
import type { GameLog } from '../../hooks/useGame'

interface Props {
  log: GameLog[]
  show: boolean
}

export function ReasoningPanel({ log, show }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [log])

  if (!show) return null

  const withReasoning = log.filter(e => e.reasoning)

  return (
    <div className="cyber-panel flex flex-col h-full overflow-hidden">
      <div className="hud-label px-3 py-2 border-b border-cyber-border">AI Reasoning</div>
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
        {withReasoning.length === 0 && (
          <div className="text-cyber-dim text-xs italic">Awaiting first move...</div>
        )}
        {withReasoning.map((entry, i) => (
          <div key={i} className="text-[11px] leading-relaxed">
            <div className="flex gap-2 mb-1">
              <span className={`hud-label ${entry.side === 'player1' ? 'text-cyber-cyan' : 'text-cyber-blue'}`}>
                {entry.side === 'player1' ? 'P1' : 'P2'}
              </span>
              <span className="hud-label">T{entry.turn}</span>
              <span className={`text-[10px] uppercase ${
                entry.result === 'sunk' ? 'text-cyber-orange' :
                entry.result === 'hit'  ? 'text-cyber-red' :
                'text-cyber-dim'
              }`}>{entry.result}</span>
              <span className="text-cyber-dim">({entry.row},{entry.col})</span>
            </div>
            <div className="text-cyber-dim border-l-2 border-cyber-border pl-2">
              {entry.reasoning}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
