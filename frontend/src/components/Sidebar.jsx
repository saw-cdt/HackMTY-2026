import BrandMark from './BrandMark'

const STAGES = [
  { key: 'running', label: 'Corriendo' },
  { key: 'result', label: 'Resultado' },
]

export default function Sidebar({ view, onNavigate, appState, onReset, leadsCount }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <BrandMark />
        <div>
          <div className="brand-name">Forensic Auditor</div>
          <div className="brand-sub">HackMTY 2026</div>
        </div>
      </div>

      <nav className="nav">
        <button
          type="button"
          className={`nav-item ${view === 'audit' ? 'active' : ''}`}
          onClick={() => onNavigate('audit')}
        >
          <span className="dot" />
          Auditoría
        </button>
        <button
          type="button"
          className={`nav-item ${view === 'leads' ? 'active' : ''}`}
          onClick={() => onNavigate('leads')}
        >
          <span className="dot" />
          Leads descartados{leadsCount ? ` (${leadsCount})` : ''}
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
          ↺ Nueva corrida
        </button>
      </div>
    </aside>
  )
}
