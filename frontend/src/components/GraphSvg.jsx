import { edgePoints } from '../lib/graph.js'
import { fmtMXNexact, fmtDate } from '../lib/format.js'
import { GRAPH_THEME } from '../lib/graphTheme.js'

function labelLines(node) {
  const parts = String(node.label || node.id).split(' · ')
  const id = parts[0] || node.id
  const rest = parts.slice(1).join(' · ')
  return { id, rest }
}

// nodeStyle/edgeStyle devuelven { stroke, fill, ... }. Si el llamador no
// define nodeStyle/edgeStyle, se usa un estilo neutro por defecto.
export default function GraphSvg({
  nodes,
  edges,
  pos,
  width = 960,
  height = 520,
  nodeStyle,
  edgeStyle,
  currency = true,
  onSelectNode,
  onSelectEdge,
  selectedId,
}) {
  const groups = {}
  for (const e of edges) {
    const k = `${e.from}|${e.to}`
    groups[k] = groups[k] || []
    groups[k].push(e)
  }
  const offsetFor = (e) => {
    const g = groups[`${e.from}|${e.to}`]
    if (!g || g.length < 2) return 0
    const i = g.indexOf(e)
    const half = (g.length - 1) / 2
    return (i - half) * 26
  }

  const isLoop = (e) => e.from === e.to
  const interactive = typeof onSelectNode === 'function' || typeof onSelectEdge === 'function'

  return (
    <svg
      className="graph-svg"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Grafo del money trail. Cada nodo y cada monto se puede seleccionar para ver su detalle."
    >
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
        </marker>
      </defs>

      {edges.map((e) => {
        const st = edgeStyle ? edgeStyle(e) : { visible: true, stroke: GRAPH_THEME.edgeDefault, opacity: 1, highlight: false }
        if (!st.visible) return null
        const a = pos[e.from]
        const b = pos[e.to]
        if (!a || !b) return null
        const P = edgePoints(e, pos)
        if (!P) return null
        const off = offsetFor(e)
        const mx = (P.x1 + P.x2) / 2
        const my = (P.y1 + P.y2) / 2
        const dx = P.x2 - P.x1
        const dy = P.y2 - P.y1
        const len = Math.max(1, Math.hypot(dx, dy))
        const cpx = mx - (dy / len) * off
        const cpy = my + (dx / len) * off

        const path = isLoop(e)
          ? `M ${a.x} ${a.y - 24} C ${a.x + 70} ${a.y - 90}, ${a.x + 70} ${a.y - 90}, ${a.x - 24} ${a.y}`
          : off === 0
            ? `M ${P.x1} ${P.y1} L ${P.x2} ${P.y2}`
            : `M ${P.x1} ${P.y1} Q ${cpx} ${cpy} ${P.x2} ${P.y2}`

        const tx = isLoop ? a.x + 110 : mx + (off === 0 ? 0 : 12)
        const ty = isLoop ? a.y - 84 : my + (off === 0 ? -14 : -20 - Math.abs(off) * 0.6)
        const selected = selectedId && selectedId === e.id
        const canPick = interactive && typeof onSelectEdge === 'function'

        return (
          <g key={e.id} style={{ color: st.stroke, cursor: canPick ? 'pointer' : 'default' }} onClick={canPick ? () => onSelectEdge(e) : undefined}>
            {/* franja invisible más ancha, solo para que el clic no dependa de acertarle a 1.3px */}
            {canPick && (
              <path d={path} fill="none" stroke="transparent" strokeWidth={18} />
            )}
            <path
              d={path}
              fill="none"
              stroke={st.stroke}
              strokeWidth={selected ? 3.4 : st.highlight ? 2.4 : 1.3}
              opacity={st.opacity}
              markerEnd="url(#arrow)"
            />
            {e.amount != null ? (
              <g>
                <rect
                  x={tx - 60}
                  y={ty - 13}
                  width={120}
                  height={24}
                  rx={6}
                  fill="var(--surface, #fff)"
                  stroke={selected ? st.stroke : 'var(--border-strong, #CBD3E8)'}
                  strokeWidth={selected ? 1.6 : 1}
                />
                <text x={tx} y={ty} textAnchor="middle" className={`edge-amt${st.highlight ? ' hot' : ''}`}>
                  {currency ? fmtMXNexact(e.amount) : String(e.amount)}
                </text>
                <text x={tx} y={ty + 10} textAnchor="middle" fontSize="9" fill="var(--text-muted, #6B75A0)" fontFamily="var(--font-mono)">
                  {e.exhibitId || ''} {e.date ? `· ${fmtDate(e.date)}` : ''}
                </text>
              </g>
            ) : null}
          </g>
        )
      })}

      {nodes.map((n) => {
        const st = nodeStyle ? nodeStyle(n) : { stroke: GRAPH_THEME.fallback.stroke, fill: GRAPH_THEME.fallback.fill, opacity: 1, r: 20, text: GRAPH_THEME.fallback.text }
        const p = pos[n.id]
        if (!p || st.hidden) return null
        const { id, rest } = labelLines(n)
        const r = st.r || 20
        const dim = st.dim ? '0.4' : st.opacity ?? '1'
        const selected = selectedId && selectedId === n.id
        const canPick = interactive && typeof onSelectNode === 'function'
        return (
          <g
            key={n.id}
            opacity={dim}
            style={{ cursor: canPick ? 'pointer' : 'default' }}
            onClick={canPick ? () => onSelectNode(n) : undefined}
          >
            {selected && <circle cx={p.x} cy={p.y} r={r + 5} fill="none" stroke={st.stroke} strokeWidth={1.5} strokeDasharray="3 3" />}
            <circle cx={p.x} cy={p.y} r={r} fill={st.fill} stroke={st.stroke} strokeWidth={selected ? 2.6 : st.strokeWidth || 1.6} />
            {n.kind !== 'company' && !st.bare && (
              <text x={p.x} y={p.y + 4} textAnchor="middle" fontSize="10" fontWeight="700" fill={st.text} fontFamily="var(--font-mono)">
                {id.length > 13 ? `${id.slice(0, 12)}…` : id}
              </text>
            )}
            <text x={p.x} y={p.y + r + 14} textAnchor="middle" className="graph-label" fill={st.text2 || 'var(--text-muted, #6B75A0)'}>
              {rest.length > 34 ? `${rest.slice(0, 33)}…` : rest}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
