import { t, schemeLabel, localizeResult } from '../i18n/strings'

function findNode(model, id) {
  return model.nodes.find((n) => n.id === id)
}

// El contenido de fondo (narrativa, argumento, señal) lo redacta el
// agente siempre en español -- no se traduce al vuelo, solo la interfaz.
function Column({ kind, node, ctx, lang }) {
  const title = kind === 'accused' ? t(lang, 'colAccused') : t(lang, 'colDismissed')
  const resultText = localizeResult(lang, ctx?.result, kind)

  const signalDisplay = schemeLabel(lang, ctx?.signal) || ctx?.signal
  const whatShowed = ctx?.narrative || ctx?.rule_broken
  const argument = ctx?.challenger_argument

  return (
    <div className="contrast-card">
      <div className={`contrast-head ${kind}`}>
        <span>{title}</span>
        <span>{node?.label || '—'}</span>
      </div>
      <div className="contrast-body">
        <div className="contrast-row">
          <div className="contrast-row-label">{t(lang, 'rowSignal')}</div>
          <div className="contrast-row-value">{signalDisplay || '—'}</div>
        </div>
        <div className="contrast-row">
          <div className="contrast-row-label">{t(lang, 'rowTools')}</div>
          <div className="contrast-row-value">
            {ctx?.tool_calls_made?.length ? (
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
          <div className="contrast-row-label">{t(lang, 'rowWhatShowed')}</div>
          <div className="contrast-row-value">{whatShowed || '—'}</div>
        </div>
        <div className="contrast-row">
          <div className="contrast-row-label">{t(lang, 'rowChallengerArgued')}</div>
          <div className="contrast-row-value">{argument || '—'}</div>
        </div>
        <div className="contrast-row">
          <div className="contrast-row-label">{t(lang, 'rowResult')}</div>
          <div className="contrast-row-value" style={{ fontWeight: 700 }}>
            {resultText}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ContrastPanel({ model, lang }) {
  const accusedId = model.highlight.accused
  const dismissedId = model.highlight.dismissed
  if (!accusedId && !dismissedId) return null

  const accusedNode = findNode(model, accusedId)
  const dismissedNode = findNode(model, dismissedId)
  const accusedCtx = accusedId ? model.getContext(accusedId) : null
  const dismissedCtx = dismissedId ? model.getContext(dismissedId) : null

  return (
    <div>
      <h2 className="section-title">{t(lang, 'contrastTitle')}</h2>
      <p className="section-sub">{t(lang, 'contrastSub')}</p>
      <div className="contrast-grid">
        <Column kind="accused" node={accusedNode} ctx={accusedCtx} lang={lang} />
        <Column kind="dismissed" node={dismissedNode} ctx={dismissedCtx} lang={lang} />
      </div>
    </div>
  )
}
