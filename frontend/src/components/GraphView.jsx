import { formatMxn } from '../data/format'

const VIEW_W = 900
const VIEW_H = 584

// Cuanto se retarda la aparicion de un nodo respecto al de antes, DENTRO
// del mismo paso -- para que no salgan los 2-3 nodos de un paso todos en
// el mismo instante. 50ms cae en el rango pedido (40-60ms).
const NODE_STAGGER_MS = 50
// Cuanto tarda la etiqueta del monto en aparecer despues de que la
// arista termino de dibujarse (coincide con la duracion del trazo).
const EDGE_DRAW_MS = 400
const EDGE_DRAW_CLIMAX_MS = 750

const STATE_COLOR_VAR = {
  neutral: 'var(--state-neutral)',
  dismissed: 'var(--state-dismissed)',
  flagged: 'var(--state-flagged)',
  accused: 'var(--state-accused)',
}

const STATE_SOFT_VAR = {
  neutral: 'var(--state-neutral-soft)',
  dismissed: 'var(--state-dismissed-soft)',
  flagged: 'var(--state-flagged-soft)',
  accused: 'var(--state-accused-soft)',
}

// Un nodo "accused" solo se revela como tal hasta el ultimo paso (el
// climax). Antes de eso se ve como candidato marcado (flagged): la
// revelacion del titular se guarda para el final, nunca antes.
function visualState(node, step, maxStep) {
  if (node.type === 'company') return 'neutral'
  if (node.state === 'accused' && step < maxStep) return 'flagged'
  return node.state
}

function curvedPath(x1, y1, x2, y2, cx, cy, laneOffset = 0) {
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2
  const dx = x2 - x1
  const dy = y2 - y1
  const len = Math.hypot(dx, dy) || 1
  const nx = -dy / len
  const ny = dx / len
  const bow = Math.min(Math.max(len * 0.12, 12), 55) + laneOffset
  const cvx = mx - cx
  const cvy = my - cy
  const sign = nx * cvx + ny * cvy >= 0 ? 1 : -1
  const cpx = mx + nx * bow * sign
  const cpy = my + ny * bow * sign
  // punto de la curva a t=0.5 (no el control point) para anclar la
  // etiqueta justo sobre el trazo, no en su vertice
  const labelX = 0.25 * x1 + 0.5 * cpx + 0.25 * x2
  const labelY = 0.25 * y1 + 0.5 * cpy + 0.25 * y2
  return { d: `M ${x1},${y1} Q ${cpx},${cpy} ${x2},${y2}`, labelX, labelY }
}

// Cuando varias aristas comparten origen y destino (p. ej. el mismo
// proveedor recibe 5 pagos), las abre en abanico para que no se dibujen
// exactamente encima unas de otras.
function laneOffsetsFor(edges) {
  const groups = new Map()
  edges.forEach((e) => {
    const key = `${e.from}->${e.to}`
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(e.id)
  })
  const offsets = new Map()
  groups.forEach((ids) => {
    const n = ids.length
    ids.forEach((id, i) => {
      offsets.set(id, (i - (n - 1) / 2) * 22)
    })
  })
  return offsets
}

function amountLabelWidth(text) {
  return Math.max(34, text.length * 6.4)
}

// Retardo de entrada por nodo: los que comparten "step" no aparecen
// todos en el mismo instante, sino uno tras otro (ver NODE_STAGGER_MS).
// El orden depende del orden de `nodes` (ya estable desde el adaptador),
// no de nada aleatorio -- la misma corrida siempre anima igual.
function staggerDelaysFor(nodes) {
  const seen = new Map()
  const delays = new Map()
  nodes.forEach((n) => {
    const i = seen.get(n.step) || 0
    delays.set(n.id, i * NODE_STAGGER_MS)
    seen.set(n.step, i + 1)
  })
  return delays
}

export default function GraphView({ model, step, onSelectNode, selectedId }) {
  const { nodes, edges, maxStep, companyId } = model
  const company = nodes.find((n) => n.id === companyId)
  const laneOffsets = laneOffsetsFor(edges)
  const staggerDelays = staggerDelaysFor(nodes)

  return (
    <div className="card graph-card">
      <div className="graph-legend">
        {['neutral', 'dismissed', 'flagged', 'accused'].map((s) => (
          <span className="graph-legend-item" key={s}>
            <span className="graph-legend-swatch" style={{ background: STATE_COLOR_VAR[s] }} />
            {{
              neutral: 'Sin evaluar',
              dismissed: 'Descartado',
              flagged: 'Candidato',
              accused: 'Hallazgo',
            }[s]}
          </span>
        ))}
      </div>

      <div className="graph-svg-wrap">
        <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} width="100%" role="img" aria-label="Grafo de la investigación">
          {edges.map((edge) => {
            const visible = edge.step <= step
            const from = nodes.find((n) => n.id === edge.from)
            const to = nodes.find((n) => n.id === edge.to)
            if (!from || !to) return null
            const fromState = visualState(from, step, maxStep)
            const toState = visualState(to, step, maxStep)
            const isHot = fromState === 'accused' || toState === 'accused'
            const color = isHot ? STATE_COLOR_VAR.accused : 'var(--border-strong)'
            const { d, labelX, labelY } = curvedPath(
              from.x,
              from.y,
              to.x,
              to.y,
              company?.x ?? 450,
              company?.y ?? 292,
              laneOffsets.get(edge.id) ?? 0
            )
            const isClimax = edge.step >= maxStep
            const drawMs = isClimax ? EDGE_DRAW_CLIMAX_MS : EDGE_DRAW_MS
            const amountText = edge.amount != null ? formatMxn(edge.amount) : null
            const labelW = amountText ? amountLabelWidth(amountText) : 0
            return (
              <g key={edge.id} style={{ opacity: visible ? 1 : 0 }}>
                {/* pathLength="1" normaliza el largo real de la curva a 1
                    unidad, para poder animar el trazo (origen -> destino)
                    con dasharray/dashoffset sin medir la geometria. */}
                <path
                  className={`graph-edge-path${isClimax ? ' is-climax' : ''}`}
                  d={d}
                  pathLength="1"
                  style={{
                    stroke: color,
                    strokeDasharray: 1,
                    strokeDashoffset: visible ? 0 : 1,
                  }}
                />
                {amountText && (
                  <g
                    className="graph-edge-label"
                    style={{ opacity: visible ? 1 : 0, transitionDelay: visible ? `${drawMs}ms` : '0ms' }}
                  >
                    <rect
                      x={labelX - labelW / 2}
                      y={labelY - 12}
                      width={labelW}
                      height={14}
                      rx={4}
                      style={{ fill: 'var(--surface)', opacity: 0.92 }}
                    />
                    <text x={labelX} y={labelY - 2} textAnchor="middle" className="graph-edge-amount">
                      {amountText}
                    </text>
                  </g>
                )}
              </g>
            )
          })}

          {nodes.map((node) => {
            const visible = node.step <= step
            const vState = visualState(node, step, maxStep)
            const isCompany = node.type === 'company'
            const r = isCompany ? 30 : 18
            const isSelected = selectedId === node.id
            const labelAbove = node.y < (company?.y ?? 292)
            const isClimax = node.step >= maxStep && !isCompany
            const delay = staggerDelays.get(node.id) ?? 0
            // el climax no usa transition (una sola curva de entrada/
            // salida): usa una animacion de keyframes real -- crece de
            // mas y se asienta, mas marcado que solo alargar la
            // duracion. Por eso NO se fija opacity/transform inline
            // aqui: los controla la animacion (.is-climax en el CSS),
            // para que no compitan con ella.
            const groupStyle = isClimax
              ? { transformOrigin: `${node.x}px ${node.y}px`, animationDelay: `${delay}ms`, cursor: visible ? 'pointer' : 'default' }
              : {
                  opacity: visible ? 1 : 0,
                  transform: visible ? 'scale(1)' : 'scale(0)',
                  transformOrigin: `${node.x}px ${node.y}px`,
                  transitionDelay: visible ? `${delay}ms` : '0ms',
                  cursor: visible ? 'pointer' : 'default',
                }

            return (
              <g
                key={node.id}
                className={`graph-node-group${isClimax ? ' is-climax' : ''}${visible ? ' is-visible' : ''}`}
                style={groupStyle}
                onClick={() => visible && onSelectNode(node.id)}
              >
                <circle
                  className="graph-node-circle"
                  cx={node.x}
                  cy={node.y}
                  r={isSelected ? r + 3 : r}
                  style={{
                    fill: isCompany ? 'var(--accent)' : STATE_SOFT_VAR[vState],
                    stroke: isCompany ? 'var(--accent-strong)' : STATE_COLOR_VAR[vState],
                    strokeWidth: isSelected ? 3 : 1.6,
                  }}
                />
                <text
                  x={node.x}
                  y={node.y + 4}
                  textAnchor="middle"
                  className="graph-node-glyph"
                  style={{ fontSize: isCompany ? 11 : 9, fill: isCompany ? '#fff' : STATE_COLOR_VAR[vState], fontWeight: 700 }}
                >
                  {isCompany ? '🏢' : node.type === 'employee' ? 'EMP' : 'PROV'}
                </text>
                <text
                  x={node.x}
                  y={labelAbove ? node.y - r - 18 : node.y + r + 14}
                  textAnchor="middle"
                  className="graph-node-label"
                >
                  {truncate(node.label, 22)}
                </text>
                {node.sublabel && (
                  <text
                    x={node.x}
                    y={labelAbove ? node.y - r - 6 : node.y + r + 26}
                    textAnchor="middle"
                    className="graph-node-sublabel"
                  >
                    {truncate(node.sublabel, 26)}
                  </text>
                )}
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}

function truncate(str, n) {
  if (!str) return ''
  return str.length > n ? `${str.slice(0, n - 1)}…` : str
}
