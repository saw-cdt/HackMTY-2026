import { useMemo, useState } from 'react'

const CLOSED_BY_BADGE = {
  investigator: 'badge-dismissed',
  challenger: 'badge-flagged',
  validator: 'badge-accused',
}

export default function LeadsList({ leads }) {
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return leads
    return leads.filter((l) => {
      return (
        l.entity?.toLowerCase().includes(q) ||
        l.entity_label?.toLowerCase().includes(q) ||
        l.signal?.toLowerCase().includes(q) ||
        l.reason?.toLowerCase().includes(q)
      )
    })
  }, [leads, query])

  return (
    <div>
      <h2 className="section-title">Leads descartados</h2>
      <p className="section-sub">
        Todo lo que el agente investigó y decidió no acusar, con la razón exacta. Busca por RFC o nombre.
      </p>

      <div className="leads-toolbar">
        <div className="leads-search">
          <span className="search-icon">🔎</span>
          <input
            type="text"
            placeholder="Buscar por RFC, nombre o señal…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <span className="leads-count">
          {filtered.length} de {leads.length}
        </span>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">No hay leads que coincidan con «{query}».</div>
      ) : (
        <div className="leads-grid">
          {filtered.map((lead) => (
            <div className="lead-card" key={lead.entity}>
              <div className="lead-card-head">
                <div>
                  <div className="lead-entity">{lead.entity}</div>
                  {lead.entity_label && <div className="lead-entity-label">{lead.entity_label}</div>}
                </div>
                <span className={`badge ${CLOSED_BY_BADGE[lead.closed_by] || 'badge-neutral'}`}>
                  {lead.closed_by}
                </span>
              </div>

              <div>
                <div className="lead-field-label">Señal</div>
                <div className="lead-reason">{lead.signal}</div>
              </div>

              <div>
                <div className="lead-field-label">Razón</div>
                <div className="lead-reason">{lead.reason}</div>
              </div>

              {lead.tool_calls_made?.length > 0 && (
                <div>
                  <div className="lead-field-label">Herramientas</div>
                  <div className="tool-pill-row">
                    {lead.tool_calls_made.map((t) => (
                      <span className="tool-pill" key={t}>
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
