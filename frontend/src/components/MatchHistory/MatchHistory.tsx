import { useEffect, useState } from 'react'
import { matchApi } from '../../api/client'
import type { MatchRecord, WinRates } from '../../types/game'

export function MatchHistory() {
  const [matches, setMatches] = useState<MatchRecord[]>([])
  const [winRates, setWinRates] = useState<WinRates>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([matchApi.list(), matchApi.winRates()])
      .then(([m, w]) => { setMatches(m); setWinRates(w) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-full text-cyber-dim text-sm">Loading...</div>
  )

  const providers = Object.entries(winRates).sort((a, b) => b[1].wins - a[1].wins)

  return (
    <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
      {/* Leaderboard */}
      <div className="cyber-panel p-4">
        <div className="hud-label mb-3 text-sm">AI Leaderboard</div>
        {providers.length === 0 ? (
          <div className="text-cyber-dim text-xs italic">No matches played yet.</div>
        ) : (
          <div className="flex flex-col gap-2">
            {providers.map(([name, stats], i) => {
              const winPct = stats.total > 0 ? Math.round((stats.wins / stats.total) * 100) : 0
              return (
                <div key={name} className="flex items-center gap-4">
                  <span className="hud-label w-4">{i + 1}</span>
                  <span className="hud-value flex-1 capitalize">{name}</span>
                  <span className="text-cyber-cyan text-xs">{stats.wins}W</span>
                  <span className="text-cyber-red text-xs">{stats.losses}L</span>
                  <div className="w-24 h-1.5 bg-cyber-border rounded-full overflow-hidden">
                    <div
                      className="h-full bg-cyber-cyan rounded-full transition-all"
                      style={{ width: `${winPct}%` }}
                    />
                  </div>
                  <span className="hud-label w-10 text-right">{winPct}%</span>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Match list */}
      <div className="cyber-panel">
        <div className="hud-label px-4 py-3 border-b border-cyber-border">Recent Matches</div>
        {matches.length === 0 ? (
          <div className="p-4 text-cyber-dim text-xs italic">No matches yet.</div>
        ) : (
          <div className="divide-y divide-cyber-border">
            {[...matches].reverse().slice(0, 50).map(m => (
              <div key={m.id} className="flex items-center gap-4 px-4 py-2 text-xs hover:bg-white/5 transition-colors">
                <span className="text-cyber-dim w-8">#{m.id}</span>
                <span className="text-cyber-dim">{m.board_size}×{m.board_size}</span>
                <span className="text-cyber-dim capitalize">{m.difficulty.replace('_', ' ')}</span>
                <span className="text-cyber-blue flex-1">
                  {m.ai_provider_1 ?? 'Human'} vs {m.ai_provider_2 ?? '?'}
                </span>
                {m.winner ? (
                  <span className="text-cyber-cyan">{m.winner === 'player1' ? (m.ai_provider_1 ?? 'Human') : (m.ai_provider_2 ?? 'P2')} won</span>
                ) : (
                  <span className="text-cyber-dim italic">in progress</span>
                )}
                {m.total_turns && <span className="text-cyber-dim">{m.total_turns} turns</span>}
                <span className="text-cyber-dim">{new Date(m.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
