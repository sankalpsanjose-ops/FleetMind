import { useState, useCallback } from 'react'
import type { Orientation, ShipPlacement } from '../../types/game'

interface ShipDef {
  ship_type: string
  size: number
  label: string
}

const STANDARD_FLEET: ShipDef[] = [
  { ship_type: 'carrier',    size: 5, label: 'Carrier' },
  { ship_type: 'battleship', size: 4, label: 'Battleship' },
  { ship_type: 'cruiser',    size: 3, label: 'Cruiser' },
  { ship_type: 'submarine',  size: 3, label: 'Submarine' },
  { ship_type: 'patrol',     size: 2, label: 'Patrol' },
]

interface Props {
  boardSize: number
  onConfirm: (placements: ShipPlacement[]) => void
  onRandomize: () => void
}

interface CellPos { row: number; col: number }

export function FleetPlacement({ boardSize, onConfirm, onRandomize }: Props) {
  const [placements, setPlacements] = useState<ShipPlacement[]>([])
  const [selected, setSelected] = useState<ShipDef | null>(STANDARD_FLEET[0])
  const [orientation, setOrientation] = useState<Orientation>('horizontal')
  const [hovered, setHovered] = useState<CellPos | null>(null)

  const placedTypes = new Set(placements.map(p => p.ship_type))
  const remaining = STANDARD_FLEET.filter(s => !placedTypes.has(s.ship_type))

  const cellSize = Math.min(40, Math.floor(480 / boardSize))

  const getPreviewCells = useCallback((): CellPos[] => {
    if (!selected || !hovered) return []
    const cells: CellPos[] = []
    for (let i = 0; i < selected.size; i++) {
      const r = orientation === 'horizontal' ? hovered.row : hovered.row + i
      const c = orientation === 'horizontal' ? hovered.col + i : hovered.col
      if (r >= boardSize || c >= boardSize) return []
      cells.push({ row: r, col: c })
    }
    return cells
  }, [selected, hovered, orientation, boardSize])

  const occupiedCells = useCallback((): Set<string> => {
    const s = new Set<string>()
    for (const p of placements) {
      for (let i = 0; i < STANDARD_FLEET.find(f => f.ship_type === p.ship_type)!.size; i++) {
        const r = p.orientation === 'horizontal' ? p.row : p.row + i
        const c = p.orientation === 'horizontal' ? p.col + i : p.col
        s.add(`${r},${c}`)
      }
    }
    return s
  }, [placements])

  const handleCellClick = (row: number, col: number) => {
    if (!selected) return
    const preview = getPreviewCells()
    if (preview.length !== selected.size) return
    const occupied = occupiedCells()
    if (preview.some(p => occupied.has(`${p.row},${p.col}`))) return

    setPlacements(prev => [
      ...prev,
      { ship_type: selected.ship_type, orientation, row, col }
    ])
    const nextShip = STANDARD_FLEET.find(s => !placedTypes.has(s.ship_type) && s.ship_type !== selected.ship_type)
    setSelected(nextShip ?? null)
  }

  const handleUndo = () => {
    if (placements.length === 0) return
    const last = placements[placements.length - 1]
    setPlacements(prev => prev.slice(0, -1))
    const ship = STANDARD_FLEET.find(s => s.ship_type === last.ship_type)
    if (ship) setSelected(ship)
  }

  const preview = getPreviewCells()
  const previewSet = new Set(preview.map(p => `${p.row},${p.col}`))
  const occupied = occupiedCells()

  const isReady = remaining.length === 0

  return (
    <div className="flex flex-col gap-4 items-center">
      <div className="hud-label text-center tracking-[0.3em]">Place Your Fleet</div>

      <div className="flex gap-6 items-start">
        {/* Ship list */}
        <div className="flex flex-col gap-2 min-w-[140px]">
          {STANDARD_FLEET.map(ship => {
            const placed = placedTypes.has(ship.ship_type)
            const isActive = selected?.ship_type === ship.ship_type
            return (
              <button
                key={ship.ship_type}
                onClick={() => !placed && setSelected(ship)}
                disabled={placed}
                className={`text-left px-3 py-2 border text-xs uppercase tracking-wider transition-all
                  ${placed ? 'opacity-30 border-cyber-border text-cyber-dim cursor-default' :
                    isActive ? 'border-cyber-cyan text-cyber-cyan bg-cyber-cyan/10' :
                    'border-cyber-border text-cyber-dim hover:border-cyber-cyan hover:text-cyber-cyan cursor-pointer'
                  }`}
              >
                <div>{ship.label}</div>
                <div className="flex gap-0.5 mt-1">
                  {Array.from({ length: ship.size }).map((_, i) => (
                    <div key={i} className={`w-3 h-2 border ${placed ? 'border-cyber-border bg-cyber-border/30' : isActive ? 'border-cyber-cyan bg-cyber-cyan/40' : 'border-cyber-dim'}`} />
                  ))}
                </div>
              </button>
            )
          })}

          <button
            onClick={() => setOrientation(o => o === 'horizontal' ? 'vertical' : 'horizontal')}
            className="cyber-btn text-xs mt-2"
          >
            Rotate [{orientation === 'horizontal' ? 'H' : 'V'}]
          </button>
        </div>

        {/* Grid */}
        <div
          className="border border-cyber-border"
          style={{ display: 'grid', gridTemplateColumns: `repeat(${boardSize}, ${cellSize}px)` }}
        >
          {Array.from({ length: boardSize }).map((_, r) =>
            Array.from({ length: boardSize }).map((_, c) => {
              const key = `${r},${c}`
              const isOccupied = occupied.has(key)
              const isPreview = previewSet.has(key)
              const isConflict = isPreview && isOccupied
              return (
                <div
                  key={key}
                  onClick={() => handleCellClick(r, c)}
                  onMouseEnter={() => setHovered({ row: r, col: c })}
                  onMouseLeave={() => setHovered(null)}
                  style={{ width: cellSize, height: cellSize }}
                  className={`border border-[rgba(0,255,180,0.15)] cursor-crosshair transition-colors
                    ${isConflict  ? 'bg-cyber-red/40' :
                      isPreview   ? 'bg-cyber-cyan/20 border-cyber-cyan/60' :
                      isOccupied  ? 'bg-cyber-blue/30 border-cyber-blue/50' :
                      'bg-[#011822] hover:bg-cyber-cyan/5'
                    }`}
                />
              )
            })
          )}
        </div>
      </div>

      <div className="flex gap-3">
        <button onClick={handleUndo} disabled={placements.length === 0} className="cyber-btn">Undo</button>
        <button onClick={onRandomize} className="cyber-btn">Randomize</button>
        <button onClick={() => onConfirm(placements)} disabled={!isReady} className="cyber-btn">
          {isReady ? 'Confirm Fleet' : `Place ${remaining.length} more`}
        </button>
      </div>
    </div>
  )
}
