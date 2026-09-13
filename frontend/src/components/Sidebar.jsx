import BrandMark from './BrandMark'
import { t } from '../i18n/strings'

export default function Sidebar({ view, onNavigate, appState, onReset, leadsCount, lang }) {
  const STAGES = [
    { key: 'running', label: t(lang, 'stageRunning') },
    { key: 'result', label: t(lang, 'stageResult') },
  ]

  return (
    <aside className="sidebar">
      <div className="brand">
        <BrandMark />
        <div>
          <div className="brand-name">{t(lang, 'brandName')}</div>
          <div className="brand-sub">{t(lang, 'brandSub')}</div>
        </div>
      </div>

      <nav className="nav">
        <button
          type="button"
          className={`nav-item ${view === 'audit' ? 'active' : ''}`}
          onClick={() => onNavigate('audit')}
        >
          <span className="dot" />
          {t(lang, 'navAudit')}
        </button>
        <button
          type="button"
          className={`nav-item ${view === 'leads' ? 'active' : ''}`}
          onClick={() => onNavigate('leads')}
        >
          <span className="dot" />
          {t(lang, 'leadsTitle')}
          {leadsCount ? ` (${leadsCount})` : ''}
        </button>
      </nav>

      <div className="sidebar-footer">
        <div className="stage-tracker">
          {STAGES.map((s) => {
            const done =
              (s.key === 'running' && appState === 'result') || false
            const current = appState === s.key
            return (
              <div
                key={s.key}
                className={`stage-tracker-row ${done ? 'done' : ''} ${current ? 'current' : ''}`}
              >
                <span className="pip" />
                {s.label}
              </div>
            )
          })}
        </div>
        <button type="button" className="btn btn-ghost" onClick={onReset}>
          {t(lang, 'newRun')}
        </button>
      </div>
    </aside>
  )
}
