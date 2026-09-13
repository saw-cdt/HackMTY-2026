import { formatMxn, formatNumber, formatSeconds } from '../data/format'

export default function StatCards({ runMetadata }) {
  const cards = [
    {
      key: 'llm_calls',
      label: 'Llamadas al modelo',
      value: formatNumber(runMetadata.llm_calls),
      icon: '🧠',
      bg: 'var(--accent-soft)',
      color: 'var(--accent-strong)',
      hint: runMetadata.model || 'Ollama local',
    },
    {
      key: 'mxn_cost',
      label: 'Costo',
      value: formatMxn(runMetadata.mxn_cost ?? 0),
      icon: '💳',
      bg: 'var(--state-dismissed-soft)',
      color: 'var(--state-dismissed)',
      hint: 'Modelo local, sin API externa',
    },
    {
      key: 'wall_clock_seconds',
      label: 'Tiempo total',
      value: formatSeconds(runMetadata.wall_clock_seconds),
      icon: '⏱',
      bg: 'var(--state-flagged-soft)',
      color: 'var(--state-flagged)',
      hint: runMetadata.deterministic ? 'Corrida determinista' : 'Corrida no determinista',
    },
  ]

  return (
    <div className="stat-grid">
      {cards.map((c) => (
        <div className="stat-card" key={c.key}>
          <div className="stat-card-head">
            <span className="stat-card-label">{c.label}</span>
            <span className="stat-card-icon" style={{ background: c.bg, color: c.color }}>
              {c.icon}
            </span>
          </div>
          <div className="stat-card-value">{c.value}</div>
          <div className="stat-card-hint" style={{ color: c.color }}>
            {c.hint}
          </div>
        </div>
      ))}
    </div>
  )
}
