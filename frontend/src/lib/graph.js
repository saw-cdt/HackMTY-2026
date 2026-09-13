// Construye el modelo del grafo del caso (y del trail de un hallazgo) a
// partir del submission canónico + opcional estate (para resolver CLABEs).
// El layout es POSICIONES FIJAS calculadas una vez — sin auto-layout que
// reacomode al aparecer un nodo (restricción de la demo).

const COMPANY_UID = 'company'

function resolveClabe(clabe, estate) {
  if (!estate || !estate.clabeIndex) return null
  return estate.clabeIndex[clabe] || null
}

function nodeLabel(ref, fallbackLabel, estate) {
  if (fallbackLabel) return fallbackLabel
  if (estate && estate.nameByRfc && ref.startsWith('RFC:')) {
    const name = estate.nameByRfc[ref]
    if (name) return `${ref} · ${name}`
  }
  return ref
}

export function buildTrailGraph(finding, estate) {
  const nodes = new Map()
  const edges = []
  const getNode = (ref, label, kind) => {
    const id = ref || `anon-${nodes.size}`
    if (!nodes.has(id)) {
      nodes.set(id, { id, kind, label: label || ref || '—' })
    }
    return id
  }

  for (const s of finding.moneyTrail || []) {
    const fromRes = resolveClabe(s.from, estate)
    const toRes = resolveClabe(s.to, estate)

    let kindFrom = 'clabe'
    if (fromRes?.kind === 'company') kindFrom = 'company'
    else if (fromRes?.kind === 'employee') kindFrom = 'employee'
    else if (fromRes?.kind === 'vendor') kindFrom = 'entity'

    let kindTo = 'clabe'
    if (toRes?.kind === 'company') kindTo = 'company'
    else if (toRes?.kind === 'employee') kindTo = 'employee'
    else if (toRes?.kind === 'vendor') kindTo = 'entity'

    const fromLabel =
      s.fromLabel ||
      (fromRes
        ? fromRes.label
        : s.from && s.from.length === 18
          ? `CLABE ····${s.from.slice(-4)}`
          : s.from)

    const toLabel =
      s.toLabel ||
      (toRes
        ? toRes.label
        : s.to && s.to.length === 18
          ? `CLABE ····${s.to.slice(-4)}`
          : s.to)

    const from = getNode(s.from, fromLabel, kindFrom)
    const to = getNode(s.to, toLabel, kindTo)
    edges.push({
      id: s.exhibitId || `E${edges.length}`,
      from, to,
      amount: s.amount, date: s.date, note: s.note,
      exhibitId: s.exhibitId,
    })
  }

  for (const ent of finding.entities || []) {
    if (!nodes.has(ent)) {
      nodes.set(ent, {
        id: ent,
        kind: ent.startsWith('EMP:') ? 'employee' : 'entity',
        label: nodeLabel(ent, null, estate),
      })
    }
  }

  return { nodes: [...nodes.values()], edges }
}

export function buildCaseGraph(submission, estate) {
  const nodes = []
  const edges = []
  const seen = new Set()

  const company = {
    id: COMPANY_UID,
    kind: 'company',
    label: submission.companyLabel || submission.companyRfc || 'EMPRESA INVESTIGADA',
    rfc: submission.companyRfc,
  }
  nodes.push(company)
  seen.add(COMPANY_UID)

  const maxNodes = 14
  const addEntity = (ref, { scheme, found = true } = {}) => {
    if (seen.has(ref)) return
    if (nodes.length >= maxNodes) return
    seen.add(ref)
    nodes.push({
      id: ref,
      kind: ref.startsWith('EMP:') ? 'employee' : 'entity',
      label: nodeLabel(ref, null, estate),
      rfc: ref,
      scheme,
      found,
    })
  }

  const findingsSorted = [...(submission.findings || [])].sort(
    (a, b) => (b.pesoAmount || 0) - (a.pesoAmount || 0),
  )

  for (const f of findingsSorted) {
    for (const ent of f.entities || []) {
      addEntity(ent, { scheme: f.schemeType, found: true })
    }
  }

  for (const lead of submission.leads || []) {
    addEntity(lead.entity, { scheme: null, found: false })
  }

  for (const f of findingsSorted) {
    for (const s of f.moneyTrail || []) {
      const fromRes = resolveClabe(s.from, estate)
      const toRes = resolveClabe(s.to, estate)
      let fromId = s.from
      let toId = s.to
      if (fromRes?.kind === 'company') fromId = COMPANY_UID
      else if (fromRes?.kind === 'vendor' && fromRes.rfc) fromId = fromRes.rfc
      if (toRes?.kind === 'company') toId = COMPANY_UID
      else if (toRes?.kind === 'vendor' && toRes.rfc) toId = toRes.rfc

      if (!seen.has(fromId)) {
        if (nodes.length < maxNodes) {
          seen.add(fromId)
          nodes.push({
            id: fromId, kind: 'clabe',
            label: resolveClabe(s.from, estate)?.label || (s.fromLabel || `CLABE ····${s.from?.slice(-4) || '?'}`),
          })
        }
      }
      if (!seen.has(toId)) {
        if (nodes.length < maxNodes) {
          seen.add(toId)
          nodes.push({
            id: toId, kind: 'clabe',
            label: resolveClabe(s.to, estate)?.label || (s.toLabel || `CLABE ····${s.to?.slice(-4) || '?'}`),
          })
        }
      }
      edges.push({
        id: s.exhibitId || `${fromId}>${toId}`,
        from: fromId, to: toId,
        amount: s.amount, date: s.date, note: s.note,
        findingId: f.id, schemeType: f.schemeType,
      })
    }
  }

  return { nodes, edges }
}

export function layoutGraph({ nodes, edges }, opts = {}) {
  const w = opts.width || 960
  const h = opts.height || 520
  const cx = w / 2
  const cy = h / 2
  const pos = {}

  const company = nodes.find((n) => n.kind === 'company')
  if (company) pos[company.id] = { x: cx, y: cy }

  const candidates = nodes.filter((n) => n.kind !== 'company')
  const inners = []
  const outers = []
  for (const n of candidates) {
    if (n.kind === 'clabe') inners.push(n)
    else outers.push(n)
  }

  outers.sort((a, b) => {
    const ea = edges.filter((e) => e.to === a.id || e.from === a.id).length
    const eb = edges.filter((e) => e.to === b.id || e.from === b.id).length
    return ea - eb
  })

  const angleFor = (i, n, radius) => {
    const start = -Math.PI / 2
    const step = (Math.PI * 2) / Math.max(n, 1)
    const a = start + step * i
    return { x: cx + Math.cos(a) * radius, y: cy + Math.sin(a) * radius }
  }

  const rOuter = Math.min(w, h) / 2 - 62
  const rInner = 0.52 * rOuter

  outers.forEach((n, i) => {
    pos[n.id] = angleFor(i, outers.length, rOuter)
  })
  inners.forEach((n, i) => {
    pos[n.id] = angleFor(i, inners.length, rInner)
  })

  return { pos, w, h, cx, cy }
}

export function edgePoints(e, pos) {
  const a = pos[e.from]
  const b = pos[e.to]
  if (!a || !b) return null
  const dx = b.x - a.x
  const dy = b.y - a.y
  const len = Math.max(1, Math.hypot(dx, dy))
  const ux = dx / len
  const uy = dy / len
  const gap = 26
  return {
    x1: a.x + ux * gap,
    y1: a.y + uy * gap,
    x2: b.x - ux * gap,
    y2: b.y - uy * gap,
  }
}