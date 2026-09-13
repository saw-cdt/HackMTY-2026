function findNode(model, id) {
  return model.nodes.find((n) => n.id === id)
}

function Column({ kind, node, ctx }) {
  const title = kind === 'accused' ? 'Acusado' : 'Descartado'
  const resultText =
    ctx?.result || (kind === 'accused' ? 'ACUSACIÓN' : 'Cerrado por challenger')

  return (
    <div className="contrast-card">
      <div className={`contrast-head ${kind}`}>
        <span>{title}</span>
        <span>{node?.label || '—'}</span>
      </div>
      <div className="contrast-body">
        <div className="contrast-row">
          <div className="contrast-row-label">Señal que lo marcó</div>
          <div className="contrast-row-value">{ctx?.signal || '—'}</div>
        </div>
        <div className="contrast-row">
          <div className="contrast-row-label">Herramientas consultadas</div>
          <div className="contrast-row-value">
            {ctx?.tool_calls_made?.length ? (
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
          <div className="contrast-row-label">Qué mostró</div>
          <div className="contrast-row-value">{ctx?.narrative || ctx?.rule_broken || '—'}</div>
        </div>
        <div className="contrast-row">
          <div className="contrast-row-label">Retador argumentó</div>
          <div className="contrast-row-value">{ctx?.challenger_argument || '—'}</div>
        </div>
        <div className="contrast-row">
          <div className="contrast-row-label">Resultado</div>
          <div className="contrast-row-value" style={{ fontWeight: 700 }}>
            {resultText}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ContrastPanel({ model }) {
  const accusedId = model.highlight.accused
  const dismissedId = model.highlight.dismissed
  if (!accusedId && !dismissedId) return null

  const accusedNode = findNode(model, accusedId)
  const dismissedNode = findNode(model, dismissedId)
  const accusedCtx = accusedId ? model.getContext(accusedId) : null
  const dismissedCtx = dismissedId ? model.getContext(dismissedId) : null

  return (
    <div>
      <h2 className="section-title">El contraste</h2>
      <p className="section-sub">
        La misma pregunta, dos respuestas: por qué a uno se le acusa y al otro se le cerró el caso.
      </p>
      <div className="contrast-grid">
        <Column kind="accused" node={accusedNode} ctx={accusedCtx} />
        <Column kind="dismissed" node={dismissedNode} ctx={dismissedCtx} />
      </div>
    </div>
  )
}
