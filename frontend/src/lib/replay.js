import { useCallback, useEffect, useRef, useState } from 'react'

export function useReplay(total, { interval = 1600, autoplay = true, resetKey } = {}) {
  const [step, setStep] = useState(autoplay ? 1 : 0)
  const [playing, setPlaying] = useState(autoplay)
  const timer = useRef(null)

  useEffect(() => {
    setStep(autoplay ? 1 : 0)
    setPlaying(autoplay)
  }, [resetKey, autoplay, total])

  useEffect(() => {
    if (!playing) return undefined
    timer.current = setInterval(() => {
      setStep((s) => {
        if (s >= total) {
          clearInterval(timer.current)
          setPlaying(false)
          return s
        }
        return s + 1
      })
    }, interval)
    return () => clearInterval(timer.current)
  }, [playing, total, interval])

  const play = useCallback(() => setPlaying(true), [])
  const pause = useCallback(() => {
    clearInterval(timer.current)
    setPlaying(false)
  }, [])
  const next = useCallback(() => {
    setStep((s) => {
      if (s >= total) return s
      return s + 1
    })
  }, [total])
  const reset = useCallback(() => {
    clearInterval(timer.current)
    setStep(autoplay ? 1 : 0)
    setPlaying(true)
  }, [autoplay])
  const goto = useCallback((s) => {
    setStep(Math.max(0, Math.min(s, total)))
    if (s >= total) setPlaying(false)
  }, [total])

  return { step, playing, play, pause, next, reset, goto }
}

export const CASE_STEPS = [
  {
    id: 1,
    title: 'El estate completo',
    text: 'La empresa al centro, todas las entidades alrededor. Todo gris: nada está decidido todavía.',
  },
  {
    id: 2,
    title: 'Los descartados se atenúan',
    text: 'El investigador limpió candidatos. Quien se desvanece no fue perseguido.',
  },
  {
    id: 3,
    title: 'Los señalados se colorean',
    text: 'Cada hallazgo se marca con el color de su esquema.',
  },
  {
    id: 4,
    title: 'Del sospechoso salen flechas',
    text: 'Se revela el money trail: el dinero sale de la empresa y pasa por cuentas intermedias.',
  },
  {
    id: 5,
    title: 'Las flechas convergen',
    text: 'Los saltos se conectan: el destino de cada paso es el origen del siguiente.',
  },
  {
    id: 6,
    title: 'El desenlace',
    text: 'Se revela el destino y el porcentaje de retorno. El hallazgo sobrevivió retador y validador.',
  },
]

export function revealForStep(step, { nodes, edges }) {
  const visibleNodes = new Set()
  const dimmed = new Set()
  const covered = new Set()
  const colored = new Set()

  if (step >= 1) for (const n of nodes) visibleNodes.add(n.id)
  if (step >= 2) for (const n of nodes) if (!n.found) dimmed.add(n.id)
  if (step >= 3) for (const n of nodes) if (n.found && n.scheme) colored.add(n.id)

  if (step >= 4) {
    const half = Math.ceil(edges.length / 2)
    edges.forEach((e, i) => {
      if (i < half) covered.add(e.id)
    })
  }
  if (step >= 5) {
    for (const e of edges) covered.add(e.id)
  }

  return { visibleNodes, dimmed, colored, covered }
}