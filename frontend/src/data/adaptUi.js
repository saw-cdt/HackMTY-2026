// Convierte un submission.json (con o sin el bloque `ui`) en un modelo listo
// para dibujar: nodos con posición fija, aristas, el par de contraste y el
// contexto para el clic de la pregunta sorpresa.
//
// Restricciones duras (ver FRONTEND.md): posiciones fijas calculadas una sola
// vez a partir de la lista completa de nodos, nunca re-acomodadas al revelar.

const STATE_RANK = { dismissed: 0, flagged: 1, accused: 1, neutral: 2 }

function entityId(raw) {
  if (!raw) return raw
  return raw.startsWith('RFC:') || raw.startsWith('EMP:') || raw.startsWith('COMPANY:')
    ? raw
    : `RFC:${raw}`
}

function layoutRing(nodes, companyId) {
  const cx = 450
  const cy = 292
  const rx = 340
  const ry = 210

  const company = nodes.find((n) => n.id === companyId)
  const others = nodes
    .filter((n) => n.id !== companyId)
    .slice()
    .sort((a, b) => {
      const ra = STATE_RANK[a.state] ?? 2
      const rb = STATE_RANK[b.state] ?? 2
      if (ra !== rb) return ra - rb
      return a.id.localeCompare(b.id)
    })

  const n = others.length || 1
  others.forEach((node, i) => {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / n
    node.x = Math.round(cx + rx * Math.cos(angle))
    node.y = Math.round(cy + ry * Math.sin(angle))
  })

  if (company) {
    company.x = cx
    company.y = cy
  }

  return { cx, cy }
}

function maxOf(list, fn, fallback = 1) {
  if (!list.length) return fallback
  return list.reduce((m, item) => Math.max(m, fn(item) || 0), fallback)
}

function buildFromUiBlock(submission) {
  const ui = submission.ui
  const companyId = 'COMPANY'
  const nodes = [
    {
      id: companyId,
      label: ui.company?.name || submission.company_label || 'Empresa investigada',
      sublabel: ui.company?.rfc || submission.company_rfc || '',
      type: 'company',
      state: 'neutral',
      step: 1,
    },
    ...ui.nodes.map((n) => ({ ...n, id: entityId(n.id) })),
  ]

  const edges = ui.edges.map((e, i) => ({
    id: `E${i}`,
    from: e.from === (ui.company?.rfc) ? companyId : entityId(e.from),
    to: e.to === (ui.company?.rfc) ? companyId : entityId(e.to),
    amount: e.amount,
    date: e.date,
    exhibitId: e.exhibit_id,
    step: e.step ?? 4,
  }))

  layoutRing(nodes, companyId)

  const maxStep = Math.max(
    maxOf(nodes, (n) => n.step, 6),
    maxOf(edges, (e) => e.step, 6),
    6
  )

  const highlight = {
    accused: ui.highlight?.accused ? entityId(ui.highlight.accused) : null,
    dismissed: ui.highlight?.dismissed ? entityId(ui.highlight.dismissed) : null,
  }

  const context = {}
  Object.entries(ui.context || {}).forEach(([id, v]) => {
    context[entityId(id)] = v
  })

  return { nodes, edges, highlight, context, maxStep, companyId }
}

function labelFromEntity(id, findings, leads) {
  for (const f of findings) {
    const idx = (f.entities || []).indexOf(id)
    if (idx !== -1) return null // sin label individual disponible en este formato
  }
  return null
}

// Deriva un modelo de grafo cuando el submission.json todavia no trae el
// bloque `ui` (formato oficial puro). Es un respaldo: agrupa por estado,
// posiciones fijas por orden estable, sin inventar juicios nuevos.
function buildFromFindingsOnly(submission) {
  const companyId = 'COMPANY'
  const companyRfc = submission.company_rfc || ''
  const companyLabel = (submission.company_label || 'Empresa investigada').split('·')[0].trim()

  const nodeMap = new Map()
  nodeMap.set(companyId, {
    id: companyId,
    label: companyLabel,
    sublabel: companyRfc,
    type: 'company',
    state: 'neutral',
    step: 1,
  })

  const clabeToId = new Map()
  const edges = []
  const findings = submission.findings || []
  const leads = submission.leads_not_pursued || []

  findings.forEach((f) => {
    ;(f.entities || []).forEach((rawId) => {
      const id = entityId(rawId)
      if (!nodeMap.has(id)) {
        nodeMap.set(id, {
          id,
          label: id.replace(/^RFC:|^EMP:/, ''),
          sublabel: f.scheme_type,
          type: id.startsWith('EMP:') ? 'employee' : 'vendor',
          state: 'accused',
          step: 3,
        })
      }
    })
  })

  leads.forEach((lead) => {
    const id = entityId(lead.entity)
    if (!nodeMap.has(id)) {
      nodeMap.set(id, {
        id,
        label: (lead.entity_label || id.replace(/^RFC:|^EMP:/, '')).split('·')[0].trim(),
        sublabel: lead.signal,
        type: id.startsWith('EMP:') ? 'employee' : 'vendor',
        state: 'dismissed',
        step: 2,
      })
    }
  })

  findings.forEach((f) => {
    ;(f.money_trail || []).forEach((hop, i) => {
      let fromId = clabeToId.get(hop.from)
      let toId = clabeToId.get(hop.to)
      if (!fromId) fromId = hop.from === companyRfc ? companyId : guessNodeFromLabel(hop.from_label, nodeMap) || companyId
      if (!toId) toId = hop.to === companyRfc ? companyId : guessNodeFromLabel(hop.to_label, nodeMap) || companyId
      clabeToId.set(hop.from, fromId)
      clabeToId.set(hop.to, toId)
      edges.push({
        id: `${f.scheme_type}-${i}`,
        from: fromId,
        to: toId,
        amount: hop.amount,
        date: hop.date,
        exhibitId: hop.exhibit_id,
        step: i === 0 ? 4 : 5,
      })
    })
  })

  const nodes = Array.from(nodeMap.values())
  layoutRing(nodes, companyId)

  const highlight = {
    accused: findings[0] ? entityId(findings[0].entities[0]) : null,
    dismissed: leads[0] ? entityId(leads[0].entity) : null,
  }

  return { nodes, edges, highlight, context: {}, maxStep: 6, companyId }
}

function guessNodeFromLabel(label, nodeMap) {
  if (!label) return null
  const token = label.split('·')[0].trim()
  for (const [id] of nodeMap) {
    if (id.includes(token)) return id
  }
  return null
}

function buildContextFor(id, model, submission) {
  const findings = submission.findings || []
  const leads = submission.leads_not_pursued || []

  const explicit = model.context[id]
  if (explicit) {
    // ui.context (FRONTEND.md) nunca trae narrative/rule_broken -- solo
    // signal/tool_calls_made/challenger_argument/result. Se enriquece con
    // el finding real para que "Que mostro" no salga vacio; explicit gana
    // si algun dia ui.context si los trae (ej. una demo escrita a mano).
    const finding = findings.find((f) => (f.entities || []).map(entityId).includes(id))
    return {
      source: 'ui',
      ...explicit,
      narrative: explicit.narrative ?? finding?.narrative,
      rule_broken: explicit.rule_broken ?? finding?.rule_broken,
      peso_amount: explicit.peso_amount ?? finding?.peso_amount,
    }
  }

  const finding = findings.find((f) => (f.entities || []).map(entityId).includes(id))
  if (finding) {
    return {
      source: 'finding',
      signal: finding.scheme_type,
      tool_calls_made: finding.tool_calls_made || [],
      challenger_argument: finding.challenger?.argument || finding.challenger_argument || '',
      narrative: finding.narrative,
      rule_broken: finding.rule_broken,
      peso_amount: finding.peso_amount,
      result: 'ACUSACIÓN',
    }
  }

  const lead = leads.find((l) => entityId(l.entity) === id)
  if (lead) {
    return {
      source: 'lead',
      signal: lead.signal,
      tool_calls_made: lead.tool_calls_made || [],
      challenger_argument: lead.reason,
      result: `cerrado por ${lead.closed_by}`,
    }
  }

  return null
}

export function adaptSubmission(submission) {
  const model = submission.ui
    ? buildFromUiBlock(submission)
    : buildFromFindingsOnly(submission)

  return {
    ...model,
    companyLabel:
      model.nodes.find((n) => n.type === 'company')?.label ||
      submission.company_label ||
      'Empresa investigada',
    companyRfc: submission.ui?.company?.rfc || submission.company_rfc || '',
    period: submission.period || '',
    runMetadata: submission.run_metadata || {},
    findings: submission.findings || [],
    leadsNotPursued: submission.leads_not_pursued || [],
    getContext: (id) => buildContextFor(id, model, submission),
  }
}
