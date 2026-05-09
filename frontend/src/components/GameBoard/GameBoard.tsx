import { useEffect, useRef } from 'react'
import * as PIXI from 'pixi.js'
import type { AttackGrid, CellState } from '../../types/game'

interface Props {
  boardSize: number
  attackGrid: Record<string, CellState>   // "row,col" -> state
  side: 'player1' | 'player2'
  label: string
  onCellClick?: (row: number, col: number) => void
  interactive?: boolean
}

const COLORS = {
  bg:       0x000510,
  grid:     0x00ffb4,
  gridDim:  0x003322,
  hit:      0xff3333,
  miss:     0x004455,
  sunk:     0xff8c00,
  hover:    0x00ffb4,
  unknown:  0x011822,
}

const GRID_ALPHA = 0.25

export function GameBoard({ boardSize, attackGrid, label, onCellClick, interactive = false }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const appRef = useRef<PIXI.Application | null>(null)
  const cellsRef = useRef<PIXI.Graphics[][]>([])
  const particleContainerRef = useRef<PIXI.Container | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const size = containerRef.current.clientWidth
    const cellSize = Math.floor(size / boardSize)
    const canvasSize = cellSize * boardSize

    const app = new PIXI.Application({
      width: canvasSize,
      height: canvasSize,
      backgroundColor: COLORS.bg,
      antialias: true,
      resolution: window.devicePixelRatio || 1,
      autoDensity: true,
    })
    appRef.current = app
    containerRef.current.appendChild(app.view as HTMLCanvasElement)

    // Grid background
    const gridBg = new PIXI.Graphics()
    app.stage.addChild(gridBg)
    gridBg.lineStyle(1, COLORS.gridDim, GRID_ALPHA)
    for (let i = 0; i <= boardSize; i++) {
      gridBg.moveTo(i * cellSize, 0)
      gridBg.lineTo(i * cellSize, canvasSize)
      gridBg.moveTo(0, i * cellSize)
      gridBg.lineTo(canvasSize, i * cellSize)
    }

    // Cell graphics
    const cells: PIXI.Graphics[][] = []
    for (let r = 0; r < boardSize; r++) {
      cells[r] = []
      for (let c = 0; c < boardSize; c++) {
        const cell = new PIXI.Graphics()
        cell.x = c * cellSize
        cell.y = r * cellSize
        app.stage.addChild(cell)
        cells[r][c] = cell

        if (interactive && onCellClick) {
          cell.eventMode = 'static'
          cell.cursor = 'crosshair'
          cell.on('pointerover', () => {
            const key = `${r},${c}`
            if (!attackGrid[key] || attackGrid[key] === 'unknown') {
              drawCell(cell, cellSize, 'hover')
            }
          })
          cell.on('pointerout', () => {
            drawCell(cell, cellSize, attackGrid[`${r},${c}`] || 'unknown')
          })
          cell.on('pointertap', () => onCellClick(r, c))
        }
      }
    }
    cellsRef.current = cells

    const particles = new PIXI.Container()
    app.stage.addChild(particles)
    particleContainerRef.current = particles

    // Border glow
    const border = new PIXI.Graphics()
    border.lineStyle(1, COLORS.grid, 0.5)
    border.drawRect(0, 0, canvasSize, canvasSize)
    app.stage.addChild(border)

    return () => {
      app.destroy(true, { children: true })
      appRef.current = null
    }
  }, [boardSize]) // eslint-disable-line

  // Update cell visuals when attackGrid changes
  useEffect(() => {
    if (!appRef.current || cellsRef.current.length === 0) return
    const size = containerRef.current!.clientWidth
    const cellSize = Math.floor(size / boardSize)

    for (let r = 0; r < boardSize; r++) {
      for (let c = 0; c < boardSize; c++) {
        const state = attackGrid[`${r},${c}`] || 'unknown'
        const cell = cellsRef.current[r]?.[c]
        if (cell) {
          drawCell(cell, cellSize, state)
          if (state === 'hit' || state === 'sunk') {
            spawnParticles(r, c, cellSize, state)
          }
        }
      }
    }
  }, [attackGrid, boardSize]) // eslint-disable-line

  function drawCell(cell: PIXI.Graphics, cellSize: number, state: CellState | 'hover') {
    cell.clear()
    const pad = 2

    switch (state) {
      case 'unknown':
        cell.beginFill(COLORS.unknown, 0.8)
        cell.drawRect(pad, pad, cellSize - pad * 2, cellSize - pad * 2)
        cell.endFill()
        // Subtle inner dot
        cell.beginFill(0x004433, 0.3)
        cell.drawCircle(cellSize / 2, cellSize / 2, 1.5)
        cell.endFill()
        break
      case 'hover':
        cell.lineStyle(1, COLORS.hover, 0.8)
        cell.beginFill(COLORS.hover, 0.1)
        cell.drawRect(pad, pad, cellSize - pad * 2, cellSize - pad * 2)
        cell.endFill()
        break
      case 'miss':
        cell.beginFill(COLORS.miss, 0.8)
        cell.drawRect(pad, pad, cellSize - pad * 2, cellSize - pad * 2)
        cell.endFill()
        // X mark
        cell.lineStyle(1, 0x00aacc, 0.5)
        cell.moveTo(pad + 3, pad + 3)
        cell.lineTo(cellSize - pad - 3, cellSize - pad - 3)
        cell.moveTo(cellSize - pad - 3, pad + 3)
        cell.lineTo(pad + 3, cellSize - pad - 3)
        break
      case 'hit':
        cell.beginFill(COLORS.hit, 0.9)
        cell.drawRect(pad, pad, cellSize - pad * 2, cellSize - pad * 2)
        cell.endFill()
        // Center cross
        cell.lineStyle(2, 0xffaaaa, 0.8)
        cell.moveTo(cellSize / 2, pad + 3)
        cell.lineTo(cellSize / 2, cellSize - pad - 3)
        cell.moveTo(pad + 3, cellSize / 2)
        cell.lineTo(cellSize - pad - 3, cellSize / 2)
        break
      case 'sunk':
        cell.beginFill(COLORS.sunk, 0.9)
        cell.drawRect(pad, pad, cellSize - pad * 2, cellSize - pad * 2)
        cell.endFill()
        // Skull-ish: filled square with dark center
        cell.beginFill(0x331100, 0.5)
        cell.drawRect(pad + 4, pad + 4, cellSize - pad * 2 - 8, cellSize - pad * 2 - 8)
        cell.endFill()
        break
    }

    // Clickable hit area
    cell.hitArea = new PIXI.Rectangle(0, 0, cellSize, cellSize)
  }

  function spawnParticles(row: number, col: number, cellSize: number, state: CellState) {
    const container = particleContainerRef.current
    if (!container || !appRef.current) return
    const color = state === 'sunk' ? COLORS.sunk : COLORS.hit
    const cx = col * cellSize + cellSize / 2
    const cy = row * cellSize + cellSize / 2
    const count = state === 'sunk' ? 12 : 6

    for (let i = 0; i < count; i++) {
      const p = new PIXI.Graphics()
      p.beginFill(color, 0.9)
      p.drawCircle(0, 0, Math.random() * 2 + 1)
      p.endFill()
      p.x = cx
      p.y = cy
      const angle = (Math.PI * 2 * i) / count + Math.random() * 0.5
      const speed = Math.random() * 3 + 1
      const vx = Math.cos(angle) * speed
      const vy = Math.sin(angle) * speed
      container.addChild(p)

      let life = 40
      const tick = () => {
        life--
        p.x += vx
        p.y += vy
        p.alpha = life / 40
        if (life <= 0) {
          appRef.current!.ticker.remove(tick)
          container.removeChild(p)
          p.destroy()
        }
      }
      appRef.current.ticker.add(tick)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="hud-label text-center tracking-[0.3em]">{label}</div>
      <div
        ref={containerRef}
        className="w-full aspect-square border border-cyber-border rounded-sm overflow-hidden"
        style={{ imageRendering: 'pixelated' }}
      />
    </div>
  )
}
