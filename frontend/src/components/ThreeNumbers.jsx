import { CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react'
import { fmtMXN, fmtNum, fmtSec } from '../lib/format.js'

export default function ThreeNumbers({ run }) {
  if (!run) return null
  const det = run.deterministic
  return (
    <div className="card flat grid grid-3 trinums">
      <div className="trinum">
        <div className="label">Llamadas al modelo</div>
        <div className="value">{fmtNum(run.llmCalls)}</div>
        <div className="hint">llm_calls · todas pasan por el caché sha256</div>
      </div>
      <div className="trinum">
        <div className="label">Costo por corrida</div>
        <div className="value">
          {run.mxnCost === 0 ? '0' : fmtMXN(run.mxnCost)}
          <small> MXN</small>
        </div>
        <div className="hint">mxn_cost · Ollama local, los datos no salen de la red</div>
      </div>
      <div className="trinum">
        <div className="label">Tiempo de reloj</div>
        <div className="value">{fmtSec(run.wallClockSeconds)}</div>
        <div className="hint">
          wall_clock_seconds ·{' '}
          {det === true ? (
            <span className="ok"><CheckCircle2 size={12} aria-hidden="true" /> corrida determinista</span>
          ) : det === false ? (
            <span className="danger"><AlertTriangle size={12} aria-hidden="true" /> no determinista</span>
          ) : (
            <span className="muted"><HelpCircle size={12} aria-hidden="true" /> determinismo no declarado</span>
          )}
        </div>
      </div>
    </div>
  )
}
