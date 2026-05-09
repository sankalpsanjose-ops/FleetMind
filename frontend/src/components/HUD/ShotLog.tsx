import { useEffect, useRef } from 'react'
import type { GameLog } from '../../hooks/useGame'

interface Props {
  log: GameLog[]
}

export function ShotLog({ log }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [log])

  return (
    <div className="cyber-panel flex flex-col overflow-hidden" style={{ maxHeight: 240 }}>
      <div className="hud-label px-3 py-1.5 border-b border-cyber-border">Combat Log</div>
      <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-1">
        {log.length === 0 && <div className="text-cyber-dim text-[10px] italic px-1">No shots fired.</div>}
        {log.map((e, i) => (
          <div key={i} className="flex gap-2 text-[10px]">
            <span className="text-cyber-dim w-6 text-right">{e.turn}</span>
            <span className={e.side === 'player1' ? 'text-cyber-cyan' : 'text-cyber-blue'}>
              {e.side === 'player1' ? 'P1' : 'P2'}
            </span>
            <span className="text-cyber-dim">({e.row},{e.col})</span>
            <span className={
              e.result === 'sunk' ? 'text-cyber-orange font-bold' :
              e.result === 'hit'  ? 'text-cyber-red' :
              'text-cyber-dim'
            }>{e.result.toUpperCase()}</span>
            {e.shipType && <span className="text-cyber-dim">— {e.shipType}</span>}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
