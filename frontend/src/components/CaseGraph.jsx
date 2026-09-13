import { useMemo, useState } from 'react'
import { buildCaseGraph, layoutGraph } from '../lib/graph.js'
import { schemeMeta } from '../lib/schemes.js'
import { useReplay, revealForStep, CASE_STEPS } from '../lib/replay.js'
import { fmtMXNexact, fmtPct, fmtDate } from '../lib/format.js'
import { GRAPH_THEME } from '../lib/graphTheme.js'
import GraphSvg from './GraphSvg.jsx'
import GraphDetailPanel from './GraphDetailPanel.jsx'

export default function CaseGraph({ submission, estate }) {
  const activeOptions = useMemo(
    () => (submission.findings || []).filter((f) => (f.moneyTrail || []).length),
    [submission],
  )
  const [activeId, setActiveId] = useState(null)
  const [selection, setSelection] = useState(null)

  const max = CASE_STEPS.length
  const { step, playing, play, pause, next, reset, goto } = useReplay(max, { interval: 1500, autoplay: true, resetKey: activeId })

  const model = useMemo(() => {
    const g = buildCaseGraph(submission, estate)
    const layout = layoutGraph(g, { width: 960, height: 500 })
    return { nodes: g.nodes, edges: g.edges, pos: layout.pos }
  }, [submission, estate])

  const nodesById = useMemo(() => Object.fromEntries(model.nodes.map((n) => [n.id, n])), [model.nodes])

  const active = activeOptions.find((f) => f.id === activeId) || activeOptions[0]
  const activeEdges = model.edges.filter((e) => e.findingId === active?.id)

  const reveal = revealForStep(step, { nodes: model.nodes, edges: activeEdges })
  const stepDef = CASE_STEPS[Math.min(step, max) - 1]

  const nodeStyle = (n) => {
    const visible = reveal.visibleNodes.has(n.id)
    if (!visible) return { hidden: true }
    if (n.kind === 'company') {
      return { r: 30, ...GRAPH_THEME.company, strokeWidth: 2 }
    }
    if (n.kind === 'clabe') {
      if (step < 4) return { hidden: true }
      return { r: 13, ...GRAPH_THEME.clabe, bare: true }
    }
    const dimmed = reveal.dimmed.has(n.id) || n.found === false
    const colored = reveal.colored.has(n.id) && n.found !== false
    if (n.kind === 'employee') {
      return dimmed ? { r: 18, ...GRAPH_THEME.dimmed, opacity: 0.5 } : { r: 18, ...GRAPH_THEME.employee }
    }
    const colorHex = n.scheme ? schemeMeta(n.scheme).colorHex : GRAPH_THEME.fallback.stroke
    if (dimmed || n.found === false) {
      return { r: 20, ...GRAPH_THEME.dimmed, opacity: 0.55 }
    }
    return colored
      ? { r: 20, stroke: colorHex, fill: 'rgba(0,0,0,0.03)', text: colorHex, text2: GRAPH_THEME.fallback.text2, strokeWidth: 2 }
      : { r: 20, ...GRAPH_THEME.fallback }
  }

  const isReturn = (e) => {
    const to = model.nodes.find((n) => n.id === e.to)
    return to?.kind === 'company'
  }
  const edgeColorHex = (e) => (e.schemeType ? schemeMeta(e.schemeType).colorHex : GRAPH_THEME.edgeDefault)

  const edgeStyle = (e) => {
    if (e.findingId !== active?.id) return { visible: false }
    const covered = reveal.covered.has(e.id)
    if (!covered) return { visible: false }
    const ret = isReturn(e)
    return {
      visible: true,
      stroke: ret ? GRAPH_THEME.edgeReturn : edgeColorHex(e),
      opacity: ret ? 1 : 0.85,
      highlight: ret,
    }
  }

  return (
    <div className="card nopad flat">
      <div className="graph-toolbar" style={{ padding: '16px 18px 0' }}>
        <div className="row">
          <span className="chip">Grafo del caso · posiciones fijas</span>
          <span className="chip">máx. 14 nodos</span>
          {active && (
            <span className="chip">
              enfoque: <span style={{ color: schemeMeta(active.schemeType).color }}>{schemeMeta(active.schemeType).label}</span>
            </span>
          )}
        </div>
        {activeOptions.length > 1 && (
          <div className="row" style={{ marginTop: 10 }}>
            <span className="muted" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              Enfocar:
            </span>
            {activeOptions.map((f) => (
              <button key={f.id} className="chip" style={active?.id === f.id ? { borderColor: schemeMeta(f.schemeType).color, color: schemeMeta(f.schemeType).color } : {}} onClick={() => { setActiveId(f.id); setSelection(null) }}>
                <span className="swatch" style={{ background: schemeMeta(f.schemeType).color }} />
                {f.id || f.schemeType}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="graph-stage-card" style={{ margin: '14px 18px 18px' }}>
        <div className="graph-stage-head">
          <div className="steps">
            {CASE_STEPS.map((s) => (
              <button key={s.id} className={`stepdot${s.id <= step ? ' done' : ''}${s.id === step + 1 ? ' current' : ''}`} onClick={() => goto(s.id)} title={s.title}>
                {s.id}
              </button>
            ))}
          </div>
          <div style={{ flex: 1 }}>
            <h3 className="stage-title">
              {stepDef?.title || ''}
            </h3>
            <p className="stage-text">{stepDef?.text || ''}</p>
          </div>
          <div className="row">
            {playing ? (
              <button className="btn" onClick={pause}>Pausa</button>
            ) : (
              <button className="btn" onClick={play} disabled={step >= max}>Reproducir</button>
            )}
            <button className="btn" onClick={next} disabled={step >= max}>Paso →</button>
            <button className="btn" onClick={reset}>⟲</button>
          </div>
        </div>

        <div style={{ position: 'relative' }}>
          <GraphSvg
            nodes={model.nodes}
            edges={model.edges}
            pos={model.pos}
            width={960}
            height={500}
            nodeStyle={nodeStyle}
            edgeStyle={edgeStyle}
            onSelectNode={(n) => setSelection({ kind: 'node', data: n })}
            onSelectEdge={(e) => setSelection({ kind: 'edge', data: e })}
            selectedId={selection?.data?.id}
          />

          {active?.returnPct != null && step >= max && (
            <div style={{ position: 'absolute', left: '50%', top: '82%', transform: 'translate(-50%, 0)' }} className="mono">
              <span className="verdict accused">
                {fmtPct(active.returnPct)} de retorno al CLABE de la empresa
              </span>
            </div>
          )}

          {active && step >= max && (
            <div style={{ position: 'absolute', left: 16, bottom: 12 }}>
              <span className="chip" style={{ color: schemeMeta(active.schemeType).color, borderColor: schemeMeta(active.schemeType).color }}>
                {schemeMeta(active.schemeType).label} · {fmtMXNexact(active.pesoAmount)}
              </span>
            </div>
          )}
        </div>
      </div>

      <GraphDetailPanel selection={selection} estate={estate} nodesById={nodesById} />

      <div className="legend" style={{ padding: '0 18px 16px' }}>
        <span className="it"><span className="sw" style={{ background: 'var(--primary)' }} /> empresa</span>
        {activeOptions.map((f) => (
          <span className="it" key={f.id}><span className="sw" style={{ background: schemeMeta(f.schemeType).color }} /> {schemeMeta(f.schemeType).label}</span>
        ))}
        <span className="it"><span className="sw" style={{ background: 'var(--border-strong)' }} /> descartado</span>
      </div>

      {activeEdges.length > 0 && (
        <div className="tbl-scroll" style={{ padding: '0 18px 16px' }}>
          <table className="data-table" style={{ fontSize: 12 }}>
            <thead>
              <tr>
                <th>Exhibit</th>
                <th>Origen</th>
                <th>Destino</th>
                <th style={{ textAlign: 'right' }}>Monto</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {activeEdges.map((e) => (
                <tr key={e.id}>
                  <td className="key">{e.exhibitId}</td>
                  <td className="mono">{model.nodes.find((n) => n.id === e.from)?.label}</td>
                  <td className="mono">{model.nodes.find((n) => n.id === e.to)?.label}</td>
                  <td className="amt">{fmtMXNexact(e.amount)}</td>
                  <td className="mono">{fmtDate(e.date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!active && <div className="empty">No hay money trail que graficar.</div>}
    </div>
  )
}
