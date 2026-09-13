import { useMemo } from 'react'
import { CheckCircle2, ShieldAlert, AlertTriangle } from 'lucide-react'
import { schemeMeta } from '../lib/schemes.js'
import { fmtMXN, fmtDate, shortRfc } from '../lib/format.js'
import { exhibitPresence } from '../lib/estate.js'
import TrailGraph from './TrailGraph.jsx'
import ReconBox from './ReconBox.jsx'

function schemeChip({ schemeType }) {
  const m = schemeMeta(schemeType)
  return (
    <span className="chip">
      <span className="swatch" style={{ background: m.color }} />
      {m.label}
    </span>
  )
}

export default function FindingCard({ finding, estate }) {
  const m = schemeMeta(finding.schemeType)

  const presence = useMemo(() => {
    if (!estate?.db) return null
    const records = [
      ...finding.exhibits.map((e) => e.recordId),
      ...finding.moneyTrail.map((s) => s.exhibitId),
    ]
    return exhibitPresence(estate, records)
  }, [estate, finding])

  return (
    <article className="finding">
      <div className="finding-top">
        <div className="accent" style={{ background: m.color }} />
        <div className="finding-head">
          <div className="row1">
            {finding.id && <span className="chip">{finding.id}</span>}
            {schemeChip({ schemeType: finding.schemeType })}
            <span className="verdict accused">
              <CheckCircle2 size={13} aria-hidden="true" /> Acusado
            </span>
            {finding.severity && <span className="chip">{finding.severity}</span>}
          </div>
          <h3>{m.rule}</h3>
          <div className="meta">
            <span>
              entidades: {finding.entities.map((e) => (e.startsWith('EMP:') ? e : shortRfc(e))).join(' · ')}
            </span>
            <span>monto: {fmtMXN(finding.pesoAmount)}</span>
            {finding.returnPct != null && <span>retorno: {finding.returnPct}%</span>}
            <span>{finding.exhibits.length} exhibits</span>
          </div>
        </div>
      </div>

      <div className="finding-body">
        {finding.narrative && <p className="narrative">{finding.narrative}</p>}

        {finding.challenger ? (
          finding.challenger.survives ? (
            <div className="challenge">
              <div className="tag">
                <span className="verdict rejected">
                  <ShieldAlert size={13} aria-hidden="true" /> Retador · atacó y no bastó
                </span>
                Construyó la explicación inocente más fuerte que encaja con esta evidencia
              </div>
              <p>
                <strong>Argumentó:</strong> {finding.challenger.argument}
              </p>
              {finding.challenger.whyNotEnough && (
                <p className="muted">
                  <strong className="primary">Por qué no bastó:</strong> {finding.challenger.whyNotEnough}
                </p>
              )}
            </div>
          ) : (
            <div className="challenge">
              <div className="tag">
                <span className="verdict flagged">
                  <AlertTriangle size={13} aria-hidden="true" /> Inconsistencia de datos
                </span>
              </div>
              <p className="none">
                Este hallazgo trae <span className="mono">challenger.survives: false</span> pero sigue publicado en{' '}
                <span className="mono">findings[]</span>. Según el ciclo, si el retador tumba la explicación el lead
                debería cerrarse con <span className="mono">closed_by: challenger</span> y no aparecer aquí. Argumento
                registrado: {finding.challenger.argument}
              </p>
            </div>
          )
        ) : (
          <div className="challenge">
            <div className="tag">
              <span className="verdict flagged">
                <AlertTriangle size={13} aria-hidden="true" /> Inconsistencia de datos
              </span>
            </div>
            <p className="none">
              Este hallazgo no registra ataque del retador. La regla no negociable dice que ningún hallazgo se
              imprime sin pasar por retador y validador.
            </p>
          </div>
        )}

        <div className="section-head" style={{ marginTop: 6 }}>
          <span className="no" style={{ fontSize: 14 }}>→</span>
          <h2 style={{ fontSize: 16 }}>Money trail</h2>
          <span className="kicker">diagrama · clic en un nodo o un monto para el detalle</span>
        </div>
        <TrailGraph finding={finding} estate={estate} />

        <div className="section-head" style={{ marginTop: 22 }}>
          <span className="no" style={{ fontSize: 14 }}>→</span>
          <h2 style={{ fontSize: 16 }}>Exhibits</h2>
          <span className="kicker">cada uno cita su tabla y su registro</span>
        </div>
        <div className="tbl-scroll">
          <table className="exhibit-table">
            <thead>
              <tr>
                <th>Registro</th>
                <th>Tabla</th>
                <th>Fecha</th>
                <th style={{ textAlign: 'right' }}>Monto</th>
                <th>Nota</th>
                <th>Peso</th>
              </tr>
            </thead>
            <tbody>
              {finding.exhibits.map((e, i) => (
                <tr key={`${e.recordId}-${i}`}>
                  <td className="key">{e.recordId}</td>
                  <td className="mono">{e.sourceTable}</td>
                  <td className="mono">{fmtDate(e.date)}</td>
                  <td className="amt">{fmtMXN(e.amount)}</td>
                  <td className="muted">{e.note || '—'}</td>
                  <td>{e.peso ? <span className="chip chip-primary">cuenta</span> : <span className="faint">solo trail</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="peso-note">
            <span><span className="primary">cuenta</span> = suma en su tabla y se compara contra el monto del hallazgo (tolerancia 2%).</span>
            <span><span className="faint">solo trail</span> = ilumina la ruta, no suma al peso.</span>
          </div>
        </div>

        <ReconBox reconcile={finding.reconcile} pesoAmount={finding.pesoAmount} />

        {presence && (
          <div style={{ marginTop: 14 }}>
            <span className="chip">
              <span className="swatch" style={{ background: presence.missing.length ? 'var(--danger)' : 'var(--ok)' }} />
              {presence.missing.length
                ? `${presence.missing.length}/${presence.ids.length} registros citados NO existen en el estate: ${presence.missing.slice(0, 3).join(', ')}`
                : `${presence.found.size}/${presence.ids.length} registros citados existen en el estate (cotejo .db)`}
            </span>
          </div>
        )}
      </div>
    </article>
  )
}
