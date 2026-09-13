import { useState } from 'react'
import { CheckCircle2, Archive, ShieldAlert, AlertOctagon } from 'lucide-react'
import { schemeMeta, closedByMeta } from '../lib/schemes.js'
import { fmtMXN, shortRfc } from '../lib/format.js'

const CLOSED_ICON = { investigator: Archive, challenger: ShieldAlert, validator: AlertOctagon }

export default function ContrastView({ submission }) {
  const findings = submission.findings || []
  const leads = submission.leads || []

  const [fIdx, setFIdx] = useState(0)
  const [lIdx, setLIdx] = useState(0)

  if (!findings.length || !leads.length) {
    return (
      <div className="empty">
        Para el contraste hacen falta un hallazgo acusado y un lead descartado.
        <div className="mono" style={{ marginTop: 8 }}>
          este estate: {findings.length} hallazgos · {leads.length} leads
        </div>
      </div>
    )
  }

  const f = findings[Math.min(fIdx, findings.length - 1)]
  const l = leads[Math.min(lIdx, leads.length - 1)]
  const fm = schemeMeta(f.schemeType)
  const lm = closedByMeta(l.closedBy)
  const ClosedIcon = CLOSED_ICON[l.closedBy] || Archive

  const tableSet = [...new Set(f.exhibits.map((e) => e.sourceTable))].join(' · ')

  const rows = [
    {
      key: 'entity',
      label: 'Entidad señalada',
      accused: (
        <>
          <strong className="mono">{f.entities.map(shortRfc).join(' · ')}</strong>
          <div className="faint" style={{ fontSize: 11.5, marginTop: 2 }}>RFC / EMP según prefijo del formato oficial</div>
        </>
      ),
      decoy: (
        <>
          <strong className="mono">{l.entity}</strong>
          {l.entityLabel && <div className="faint" style={{ fontSize: 11.5, marginTop: 2 }}>{l.entityLabel}</div>}
        </>
      ),
    },
    {
      key: 'signal',
      label: 'Señal del detector',
      accused: <span className="mono" style={{ fontSize: 12.5 }}>{fm.label} · <span className="faint">{f.schemeType}</span></span>,
      decoy: <span className="mono" style={{ fontSize: 12.5 }}>{l.signal || '—'}</span>,
    },
    {
      key: 'docs',
      label: 'Documentos de soporte',
      accused: <span>{f.exhibits.length} exhibits · <span className="mono">{tableSet}</span></span>,
      decoy: (
        <>
          <span>{l.toolCallsMade?.length ? `${l.toolCallsMade.length} herramientas consultadas` : 'documentación revisada'}</span>
          <div className="mono faint" style={{ fontSize: 11.5, marginTop: 2 }}>{l.toolCallsMade?.join(' · ') || ''}</div>
        </>
      ),
    },
    {
      key: 'amount',
      label: 'Monto / exposición',
      accused: <span className="mono" style={{ color: fm.color }}>{fmtMXN(f.pesoAmount)}</span>,
      decoy: <span className="muted">—</span>,
    },
    {
      key: 'story',
      label: 'La historia',
      accused: <span>{f.narrative || '—'}</span>,
      decoy: <span>{l.reason || '—'}</span>,
    },
    {
      key: 'attack',
      label: 'El ataque adversarial',
      accused: f.challenger ? (
        <span>
          <span className="primary">El retador argumentó</span> y no bastó: <span className="muted">{f.challenger.argument}</span>
          {f.challenger.whyNotEnough && (
            <div className="muted" style={{ marginTop: 4 }}><em>{f.challenger.whyNotEnough}</em></div>
          )}
        </span>
      ) : (
        <span className="muted">—</span>
      ),
      decoy: <span className="muted">La explicación inocente se sostuvo y tumbó el lead.</span>,
    },
    {
      key: 'who',
      label: 'Quién decidió',
      accused: <span className="mono" style={{ color: fm.color }}>investigador → retador → validador ✓</span>,
      decoy: <span className="mono" style={{ color: lm.color }}>cerrado por {lm.label.toLowerCase()}</span>,
    },
  ]

  return (
    <div>
      <div className="note-box" style={{ marginBottom: 16 }}>
        <div className="hd">El momento central del demo</div>
        El mismo detector disparó sobre los dos. Uno es fraude y se acusó; el otro es una entidad honesta que suena igual y se descartó. Se muestran con las mismas filas, alineadas, para que la diferencia sea legible sin explicación.
      </div>

      <div className="picker-bar">
        <label>Acusado</label>
        <select value={fIdx} onChange={(e) => setFIdx(Number(e.target.value))}>
          {findings.map((x, i) => (
            <option key={i} value={i}>{x.id || x.schemeType} · {schemeMeta(x.schemeType).label} · {fmtMXN(x.pesoAmount)}</option>
          ))}
        </select>
        <label>Descartado</label>
        <select value={lIdx} onChange={(e) => setLIdx(Number(e.target.value))}>
          {leads.map((x, i) => (
            <option key={i} value={i}>{x.entity} · {x.signal || ''} · {closedByMeta(x.closedBy).label}</option>
          ))}
        </select>
      </div>

      <div className="contrast-grid">
        <div className="contrast-col accused">
          <div className="contrast-head">
            <span className="verdict accused">
              <CheckCircle2 size={13} aria-hidden="true" /> Acusado
            </span>
            <div className="t">
              <h3>{fm.label}</h3>
              <div className="sub">{f.id || f.schemeType}</div>
            </div>
          </div>
          <div className="contrast-rows">
            {rows.map((r) => (
              <div className="contrast-row" key={r.key}>
                <div className="k">{r.label}</div>
                <div className="v">{r.accused}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="contrast-col clean">
          <div className="contrast-head">
            <span className="verdict clean">
              <ClosedIcon size={13} aria-hidden="true" /> Descartado
            </span>
            <div className="t">
              <h3>{l.entityLabel || l.entity}</h3>
              <div className="sub">{l.closedBy}</div>
            </div>
          </div>
          <div className="contrast-rows">
            {rows.map((r) => (
              <div className="contrast-row" key={r.key}>
                <div className="k">{r.label}</div>
                <div className="v">{r.decoy}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
