const STATE_BADGE_CLASS = {
  neutral: 'badge-neutral',
  dismissed: 'badge-dismissed',
  flagged: 'badge-flagged',
  accused: 'badge-accused',
}

const STATE_TEXT = {
  neutral: 'Sin evaluar',
  dismissed: 'Descartado',
  flagged: 'Candidato',
  accused: 'Hallazgo',
}

export default function NodeDetailDrawer({ node, ctx, onClose }) {
  if (!node) return null

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <aside className="drawer">
        <button type="button" className="drawer-close" onClick={onClose} aria-label="Cerrar">
          ✕
        </button>
        <span className={`badge ${STATE_BADGE_CLASS[node.state] || 'badge-neutral'}`}>
          {STATE_TEXT[node.state] || node.state}
        </span>
        <div className="drawer-title">{node.label}</div>
        <div className="drawer-sub">{node.id}</div>

        {ctx ? (
          <>
            <div className="contrast-row">
              <div className="contrast-row-label">Señal</div>
              <div className="contrast-row-value">{ctx.signal || '—'}</div>
            </div>
            <div className="contrast-row">
              <div className="contrast-row-label">Herramientas consultadas</div>
              <div className="contrast-row-value">
                {ctx.tool_calls_made?.length ? (
                  <div className="tool-pill-row">
                    {ctx.tool_calls_made.map((t) => (
                      <span className="tool-pill" key={t}>
                        {t}
                      </span>
                    ))}
                  </div>
                ) : (
                  '—'
                )}
              </div>
            </div>
            <div className="contrast-row">
              <div className="contrast-row-label">Qué mostró / argumentó el retador</div>
              <div className="contrast-row-value">
                {ctx.narrative || ctx.challenger_argument || '—'}
              </div>
            </div>
            <div className="contrast-row">
              <div className="contrast-row-label">Resultado</div>
              <div className="contrast-row-value" style={{ fontWeight: 700 }}>
                {ctx.result || '—'}
              </div>
            </div>
          </>
        ) : (
          <p className="section-sub" style={{ margin: 0 }}>
            Sin contexto adicional para esta entidad.
          </p>
        )}
      </aside>
    </>
  )
}
