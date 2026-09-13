import { useMemo, useState } from 'react'
import { buildTrailGraph, layoutGraph } from '../lib/graph.js'
import { schemeMeta } from '../lib/schemes.js'
import { GRAPH_THEME } from '../lib/graphTheme.js'
import GraphSvg from './GraphSvg.jsx'
import GraphDetailPanel from './GraphDetailPanel.jsx'

export default function TrailGraph({ finding, estate }) {
  const [selection, setSelection] = useState(null)

  const model = useMemo(
    () => {
      const g = buildTrailGraph(finding, estate)
      const layout = layoutGraph(g, { width: 960, height: 460 })
      return { nodes: g.nodes, edges: g.edges, pos: layout.pos }
    },
    [finding, estate],
  )

  const nodesById = useMemo(() => Object.fromEntries(model.nodes.map((n) => [n.id, n])), [model.nodes])

  if (!model.edges.length && !finding.entities.length) {
    return <div className="empty">Sin money trail para este hallazgo.</div>
  }

  const colorHex = schemeMeta(finding.schemeType).colorHex

  const nodeStyle = (n) => {
    if (n.kind === 'company') {
      return { r: 30, ...GRAPH_THEME.company, strokeWidth: 2 }
    }
    if (n.kind === 'employee') {
      return { r: 18, ...GRAPH_THEME.employee }
    }
    if (n.kind === 'clabe') {
      return { r: 13, ...GRAPH_THEME.clabe, bare: true }
    }
    return { r: 20, stroke: colorHex, fill: 'rgba(0,0,0,0.03)', text: colorHex, text2: GRAPH_THEME.fallback.text2 }
  }

  const isReturn = (e) => {
    const to = model.nodes.find((n) => n.id === e.to)
    return to?.kind === 'company'
  }
  const edgeStyle = (e) => ({
    visible: true,
    stroke: isReturn(e) ? GRAPH_THEME.edgeReturn : colorHex,
    opacity: isReturn(e) ? 1 : 0.85,
    highlight: isReturn(e),
  })

  return (
    <div className="graph-wrap">
      <GraphSvg
        nodes={model.nodes}
        edges={model.edges}
        pos={model.pos}
        width={960}
        height={460}
        nodeStyle={nodeStyle}
        edgeStyle={edgeStyle}
        onSelectNode={(n) => setSelection({ kind: 'node', data: n })}
        onSelectEdge={(e) => setSelection({ kind: 'edge', data: e })}
        selectedId={selection?.data?.id}
      />
      <GraphDetailPanel selection={selection} estate={estate} nodesById={nodesById} />
    </div>
  )
}
