import { useState } from 'react'
import { BattleScreen } from './components/BattleScreen'
import { MatchHistory } from './components/MatchHistory/MatchHistory'

type Tab = 'game' | 'history'

export function App() {
  const [tab, setTab] = useState<Tab>('game')

  return (
    <div className="flex flex-col h-screen bg-cyber-bg text-cyber-cyan font-mono overflow-hidden">
      {/* Top nav */}
      <nav className="flex items-center gap-1 px-4 py-2 border-b border-cyber-border shrink-0">
        <span className="text-base mr-1.5 select-none" style={{ textShadow: '0 0 12px rgba(0,255,180,0.7)' }}>⚓</span>
        <span className="text-xs font-bold tracking-[0.3em] text-shadow-cyan mr-6">
          FLEET<span className="text-cyber-blue">MIND</span>
        </span>
        {(['game', 'history'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1 text-[10px] uppercase tracking-widest border transition-all
              ${tab === t
                ? 'border-cyber-cyan text-cyber-cyan bg-cyber-cyan/10'
                : 'border-transparent text-cyber-dim hover:text-cyber-cyan'
              }`}
          >
            {t === 'game' ? 'Battle' : 'History'}
          </button>
        ))}
        <div className="flex-1" />
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-cyber-cyan animate-pulse-glow" />
          <span className="hud-label">Online</span>
        </div>
      </nav>

      {/* Content */}
      <div className="flex-1 overflow-hidden relative">
        {tab === 'game' ? <BattleScreen /> : <MatchHistory />}
      </div>
    </div>
  )
}
