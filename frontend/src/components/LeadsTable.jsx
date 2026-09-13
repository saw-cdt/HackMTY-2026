import { useState } from 'react'
import { Search, Archive, ShieldAlert, AlertOctagon } from 'lucide-react'
import { closedByMeta } from '../lib/schemes.js'

const CLOSED_ICON = { investigator: Archive, challenger: ShieldAlert, validator: AlertOctagon }

export default function LeadsTable({ leads }) {
  const [only, setOnly] = useState('todos')
  const [q, setQ] = useState('')

  const filters = ['todos', ...new Set(leads.map((l) => l.closedBy))]
  const filtered = leads.filter((l) => {
    if (only !== 'todos' && l.closedBy !== only) return false
    if (q) {
      const hay = `${l.entity} ${l.signal || ''} ${l.reason || ''} ${l.entityLabel || ''}`.toLowerCase()
      if (!hay.includes(q.toLowerCase())) return false
    }
    return true
  })

  return (
    <div className="card flat nopad">
      <div className="graph-toolbar" style={{ padding: '14px 18px' }}>
        <div className="row">
          {filters.map((ft) => (
            <button key={ft} className="chip" onClick={() => setOnly(ft)} style={only === ft ? { color: 'var(--primary)', borderColor: 'var(--violet-200)', background: 'var(--violet-50)' } : {}}>
              {ft === 'todos' ? `todos (${leads.length})` : closedByMeta(ft).label}
            </button>
          ))}
        </div>
        <label className="search-input">
          <Search size={16} aria-hidden="true" />
          <input
            placeholder="buscar en razón, entidad o señal…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </label>
      </div>

      {filtered.length === 0 && (
        <div className="empty" style={{ border: 'none' }}>
          Sin leads que coincidan. <span className="mono">Una lista vacía es un resultado legítimo.</span>
        </div>
      )}

      {filtered.map((l, i) => {
        const mm = closedByMeta(l.closedBy)
        const Icon = CLOSED_ICON[l.closedBy] || Archive
        return (
          <div className="lead-row" key={i} style={{ paddingLeft: 18, paddingRight: 18 }}>
            <div>
              <div className="who">{l.entity}</div>
              <div className="faint" style={{ fontSize: 11.5 }}>{l.entityLabel || '—'}</div>
            </div>
            <div className="signal">{l.signal || '—'}</div>
            <div className="reason">{l.reason || '—'}</div>
            <div style={{ textAlign: 'right' }}>
              <span className="chip" style={{ color: mm.color, borderColor: mm.color, background: mm.soft }}>
                <Icon size={12} aria-hidden="true" /> {mm.label}
              </span>
              <div className="faint mono" style={{ fontSize: 10.5, marginTop: 6 }}>{l.toolCallsMade?.join(' · ') || ''}</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
