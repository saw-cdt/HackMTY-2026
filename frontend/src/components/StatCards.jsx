import { formatMxn, formatNumber, formatSeconds } from '../data/format'
import { t } from '../i18n/strings'

export default function StatCards({ runMetadata, lang }) {
  const cards = [
    {
      key: 'llm_calls',
      label: t(lang, 'statLlmCalls'),
      value: formatNumber(runMetadata.llm_calls),
      icon: '🧠',
      bg: 'var(--accent-soft)',
      color: 'var(--accent-strong)',
      hint: runMetadata.model || t(lang, 'statOllamaLocal'),
    },
    {
      key: 'mxn_cost',
      label: t(lang, 'statCost'),
      value: formatMxn(runMetadata.mxn_cost ?? 0),
      icon: '💳',
      bg: 'var(--state-dismissed-soft)',
      color: 'var(--state-dismissed)',
      hint: t(lang, 'statNoExternalApi'),
    },
    {
      key: 'wall_clock_seconds',
      label: t(lang, 'statTime'),
      value: formatSeconds(runMetadata.wall_clock_seconds),
      icon: '⏱',
      bg: 'var(--state-flagged-soft)',
      color: 'var(--state-flagged)',
      hint: runMetadata.deterministic ? t(lang, 'statDeterministic') : t(lang, 'statNonDeterministic'),
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
