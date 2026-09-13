import { useEffect, useRef, useState } from 'react'

// Revela paso a paso sin streaming: el JSON ya llego completo, solo se
// retarda cuando se muestra cada paso. ~50s de narracion / 6 pasos.
const STEP_DURATION_MS = 8000

export function useProgressiveSteps(maxStep, { active, onDone }) {
  const [step, setStep] = useState(active ? 1 : maxStep)
  const timerRef = useRef(null)
  const onDoneRef = useRef(onDone)
  onDoneRef.current = onDone

  useEffect(() => {
    if (!active) return undefined
    setStep(1)

    timerRef.current = setInterval(() => {
      setStep((s) => {
        if (s >= maxStep) {
          clearInterval(timerRef.current)
          onDoneRef.current?.()
          return s
        }
        return s + 1
      })
    }, STEP_DURATION_MS)

    return () => clearInterval(timerRef.current)
  }, [active, maxStep])

  const skip = () => {
    clearInterval(timerRef.current)
    setStep(maxStep)
    onDoneRef.current?.()
  }

  return { step, skip, isLast: step >= maxStep }
}
