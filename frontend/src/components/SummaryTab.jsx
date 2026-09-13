import { CheckCircle2, AlertTriangle } from 'lucide-react'
import { schemeMeta, closedByMeta } from '../lib/schemes.js'
import { fmtMXN } from '../lib/format.js'
import ThreeNumbers from './ThreeNumbers.jsx'

export default function SummaryTab({ submission, estate }) {
  const findings = submission.findings || []
  const leads = submission.leads || []
  const exposure = findings.reduce((a, f) => a + (f.pesoAmount || 0), 0)

  const byScheme = {}
  for (const f of findings) {
    byScheme[f.schemeType] = (byScheme[f.schemeType] || 0) + 1
  }
  const byClosed = {}
  for (const l of leads) {
    byClosed[l.closedBy] = (byClosed[l.closedBy] || 0) + 1
  }

  return (
    <div>
      <div className="card flat">
        <div className="between">
          <div>
            <span className="chip">{`seed ${submission.seed ?? '—'}`}</span>{' '}
            {submission.period && <span className="chip">{submission.period}</span>}
            {estate && (
              <span className="chip">
                {estate.missing.length ? <AlertTriangle size={12} aria-hidden="true" color="var(--warn)" /> : <CheckCircle2 size={12} aria-hidden="true" color="var(--ok)" />}
                {estate.fileName || 'estate .db cargado'}
              </span>
            )}
          </div>
          <div className="mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {submission.companyLabel || `EMPRESA INVESTIGADA`}
            {submission.companyRfc ? ` · ${submission.companyRfc}` : ''}
          </div>
        </div>
      </div>

      <ThreeNumbers run={submission.run} />

      <div className="grid grid-4" style={{ marginTop: 18 }}>
        <div className="stat-pill">
          <div className="v">{findings.length}</div>
          <div className="k">hallazgos publicados</div>
        </div>
        <div className="stat-pill">
          <div className="v primary">{fmtMXN(exposure)}</div>
          <div className="k">exposición total</div>
        </div>
        <div className="stat-pill">
          <div className="v">{leads.length}</div>
          <div className="k">leads no perseguidos</div>
        </div>
        <div className="stat-pill">
          <div className="v">{findings.reduce((a, f) => a + f.exhibits.length, 0)}</div>
          <div className="k">exhibits citados</div>
        </div>
      </div>

      <div className="section-head">
        <span className="no">I</span>
        <h2>Resumen ejecutivo</h2>
        <span className="kicker">lo que sobrevivió · lo que se descartó</span>
      </div>

      <div className="grid grid-2">
        <div className="card flat">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginTop: 0 }}>Hallazgos por esquema</h3>
          {Object.keys(byScheme).length === 0 && (
            <p className="muted">Lista vacía — es un resultado legítimo: si el estate no tiene fraude, no se inventa.</p>
          )}
          <div className="legend" style={{ flexDirection: 'column', gap: 10 }}>
            {Object.entries(byScheme).map(([t, n]) => {
              const mm = schemeMeta(t)
              return (
                <div key={t} className="between">
                  <span className="it">
                    <span className="sw" style={{ background: mm.color }} />
                    {mm.label}
                    <span className="faint" style={{ fontSize: 11 }}>{t}</span>
                  </span>
                  <span className="mono" style={{ color: mm.color, fontSize: 15 }}>{n}</span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="card flat">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginTop: 0 }}>Leads cerrados por capa</h3>
          <div className="legend" style={{ flexDirection: 'column', gap: 10 }}>
            {Object.entries(byClosed).map(([k, n]) => {
              const mm = closedByMeta(k)
              return (
                <div key={k} className="between">
                  <span className="it">
                    <span className="sw" style={{ background: mm.color }} />
                    {mm.label}
                  </span>
                  <span className="mono" style={{ color: mm.color, fontSize: 15 }}>{n}</span>
                </div>
              )
            })}
            {leads.length > 0 && (
              <p className="muted" style={{ fontSize: 12.5, margin: 0 }}>
                Ningún hallazgo se imprimió sin haber sido atacado: cada lead cerrado registra quién lo cerró y por qué.
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="quote">«Ningún hallazgo se imprime sin haber sido atacado. Lo que sobrevive, se publica con su prueba.»</div>
    </div>
  )
}
