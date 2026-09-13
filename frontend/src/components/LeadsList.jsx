import { useMemo, useState } from 'react'
import { t, roleLabel, schemeLabel } from '../i18n/strings'

const CLOSED_BY_BADGE = {
  investigator: 'badge-dismissed',
  challenger: 'badge-flagged',
  validator: 'badge-accused',
}

// La razón/señal las redacta el agente siempre en español -- no se
// traducen al vuelo, solo la interfaz.
function LeadCard({ lead, lang }) {
  const signalDisplay = schemeLabel(lang, lead.signal) || lead.signal
  const reason = lead.reason

  return (
    <div className="lead-card">
      <div className="lead-card-head">
        <div>
          <div className="lead-entity">{lead.entity}</div>
          {lead.entity_label && <div className="lead-entity-label">{lead.entity_label}</div>}
        </div>
        <span className={`badge ${CLOSED_BY_BADGE[lead.closed_by] || 'badge-neutral'}`}>
          {roleLabel(lang, lead.closed_by)}
        </span>
      </div>

      <div>
        <div className="lead-field-label">{t(lang, 'leadFieldSignal')}</div>
        <div className="lead-reason">{signalDisplay}</div>
      </div>

      <div>
        <div className="lead-field-label">{t(lang, 'leadFieldReason')}</div>
        <div className="lead-reason">{reason}</div>
      </div>

      {lead.tool_calls_made?.length > 0 && (
        <div>
          <div className="lead-field-label">{t(lang, 'leadFieldTools')}</div>
          <div className="tool-pill-row">
            {lead.tool_calls_made.map((call) => (
              <span className="tool-pill" key={call}>
                {call}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function LeadsList({ leads, lang }) {
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
      <h2 className="section-title">{t(lang, 'leadsTitle')}</h2>
      <p className="section-sub">{t(lang, 'leadsSub')}</p>

      <div className="leads-toolbar">
        <div className="leads-search">
          <span className="search-icon">🔎</span>
          <input
            type="text"
            placeholder={t(lang, 'leadsSearchPlaceholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <span className="leads-count">{t(lang, 'leadsCountOf', filtered.length, leads.length)}</span>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">{t(lang, 'leadsEmpty', query)}</div>
      ) : (
        <div className="leads-grid">
          {filtered.map((lead) => (
            <LeadCard lead={lead} lang={lang} key={lead.entity} />
          ))}
        </div>
      )}
    </div>
  )
}
