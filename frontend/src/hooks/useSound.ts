import { useRef, useCallback } from 'react'

export function useSound() {
  const ctxRef = useRef<AudioContext | null>(null)

  const tone = useCallback((
    freq: number,
    dur: number,
    type: OscillatorType = 'sine',
    vol = 0.25,
    freqEnd?: number,
  ) => {
    try {
      if (!ctxRef.current) ctxRef.current = new AudioContext()
      const ac = ctxRef.current
      const osc = ac.createOscillator()
      const g = ac.createGain()
      osc.connect(g)
      g.connect(ac.destination)
      osc.type = type
      osc.frequency.setValueAtTime(freq, ac.currentTime)
      if (freqEnd !== undefined) {
        osc.frequency.exponentialRampToValueAtTime(freqEnd, ac.currentTime + dur)
      }
      g.gain.setValueAtTime(vol, ac.currentTime)
      g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + dur)
      osc.start()
      osc.stop(ac.currentTime + dur)
    } catch { /* autoplay policy — silently ignored */ }
  }, [])

  const playHit = useCallback(() => {
    tone(900, 0.07, 'sawtooth', 0.35, 600)
    setTimeout(() => tone(400, 0.12, 'sine', 0.18), 65)
  }, [tone])

  const playMiss = useCallback(() => {
    tone(130, 0.18, 'sine', 0.15, 80)
    setTimeout(() => tone(95, 0.22, 'sine', 0.08), 90)
  }, [tone])

  const playSunk = useCallback(() => {
    tone(350, 0.06, 'sawtooth', 0.45, 200)
    setTimeout(() => tone(180, 0.14, 'sawtooth', 0.38, 100), 75)
    setTimeout(() => tone(90,  0.45, 'sine',     0.30, 60),  200)
  }, [tone])

  // C major arpeggio: C4 E4 G4 C5
  const playVictory = useCallback(() => {
    [523, 659, 784, 1047].forEach((f, i) =>
      setTimeout(() => tone(f, 0.55, 'sine', 0.28), i * 130)
    )
  }, [tone])

  // D minor descending: A3 F3 Eb3 D3
  const playDefeat = useCallback(() => {
    [440, 349, 311, 294].forEach((f, i) =>
      setTimeout(() => tone(f, 0.65, 'sine', 0.22), i * 170)
    )
  }, [tone])

  return { playHit, playMiss, playSunk, playVictory, playDefeat }
}
