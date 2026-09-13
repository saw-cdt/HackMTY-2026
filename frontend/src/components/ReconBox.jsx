import { CheckCircle2, AlertOctagon, HelpCircle } from 'lucide-react'
import { fmtMXNexact } from '../lib/format.js'

export default function ReconBox({ reconcile, pesoAmount }) {
  if (!reconcile) return null
  const { tables, best } = reconcile
  return (
    <div className="recon">
      <div className="head">
        Reconciliación de pesos · tolerancia 2%
        {best ? (
          best.verdict === 'ok' ? (
            <span className="ok mono"><CheckCircle2 size={13} aria-hidden="true" /> {best.table} — {fmtMXNexact(best.sum)} ≡ {fmtMXNexact(pesoAmount)}</span>
          ) : (
            <span className="danger mono"><AlertOctagon size={13} aria-hidden="true" /> sin empate al 2%</span>
          )
        ) : (
          <span className="faint mono"><HelpCircle size={13} aria-hidden="true" /> sin tabla con monto reconciliador</span>
        )}
      </div>
      <div className="rows">
        {tables.length === 0 && <span className="faint">No hay exhibits con monto reconciliador citados por tabla.</span>}
        {tables.map((t) => (
          <div className="rowbox" key={t.table}>
            <div className="t">{t.table} · {t.count} {t.count === 1 ? 'exhibit' : 'exhibits'}</div>
            <div className="v">{fmtMXNexact(t.sum)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
