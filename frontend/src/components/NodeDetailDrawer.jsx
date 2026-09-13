import { t, stateLabel, schemeLabel, localizeResult } from '../i18n/strings'

const STATE_BADGE_CLASS = {
  neutral: 'badge-neutral',
  dismissed: 'badge-dismissed',
  flagged: 'badge-flagged',
  accused: 'badge-accused',
}

// El contenido de fondo (narrativa, argumento, señal) lo redacta el
// agente siempre en español -- no se traduce al vuelo, solo la interfaz.
export default function NodeDetailDrawer({ node, ctx, onClose, lang }) {
  if (!node) return null

  const signalDisplay = ctx ? schemeLabel(lang, ctx.signal) || ctx.signal : null
  const whatOrArgued = ctx ? ctx.narrative || ctx.challenger_argument : null

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <aside className="drawer">
        <button type="button" className="drawer-close" onClick={onClose} aria-label={t(lang, 'drawerClose')}>
          ✕
        </button>
        <span className={`badge ${STATE_BADGE_CLASS[node.state] || 'badge-neutral'}`}>
          {stateLabel(lang, node.state)}
        </span>
        <div className="drawer-title">{node.label}</div>
        <div className="drawer-sub">{node.id}</div>

        {ctx ? (
          <>
            <div className="contrast-row">
              <div className="contrast-row-label">{t(lang, 'leadFieldSignal')}</div>
              <div className="contrast-row-value">{signalDisplay || '—'}</div>
            </div>
            <div className="contrast-row">
              <div className="contrast-row-label">{t(lang, 'rowTools')}</div>
              <div className="contrast-row-value">
                {ctx.tool_calls_made?.length ? (
                  <div className="tool-pill-row">
                    {ctx.tool_calls_made.map((call) => (
                      <span className="tool-pill" key={call}>
                        {call}
                      </span>
                    ))}
                  </div>
                ) : (
                  '—'
                )}
              </div>
            </div>
            <div className="contrast-row">
              <div className="contrast-row-label">{t(lang, 'drawerWhatOrArgued')}</div>
              <div className="contrast-row-value">{whatOrArgued || '—'}</div>
            </div>
            <div className="contrast-row">
              <div className="contrast-row-label">{t(lang, 'rowResult')}</div>
              <div className="contrast-row-value" style={{ fontWeight: 700 }}>
                {localizeResult(lang, ctx.result, node.state)}
              </div>
            </div>
          </>
        ) : (
          <p className="section-sub" style={{ margin: 0 }}>
            {t(lang, 'drawerNoContext')}
          </p>
        )}
      </aside>
    </>
  )
}
