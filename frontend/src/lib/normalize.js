const NUM = (v) => (v == null ? 0 : Number(v))

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null)

const pick = (obj, keys, fallback = null) => {
  if (!obj) return fallback
  for (const k of keys) {
    if (obj[k] !== undefined && obj[k] !== null) return obj[k]
  }
  return fallback
}

const toRef = (v) => {
  if (v == null) return null
  if (typeof v === 'string') return { ref: v, label: null }
  if (typeof v === 'object') {
    return {
      ref: pick(v, ['clabe', 'from', 'to', 'id', 'ref'], v.clabe ? v.clabe : null),
      label: pick(v, ['label', 'nombre', 'name'], null),
    }
  }
  return null
}

export function normalizeExhibit(e) {
  return {
    recordId: pick(e, ['record_id', 'recordId', 'id', 'folio'], null),
    sourceTable: pick(e, ['source_table', 'sourceTable', 'table'], null),
    date: pick(e, ['date', 'fecha'], null),
    amount: num(pick(e, ['amount', 'total', 'monto'], null)),
    note: pick(e, ['note', 'nota', 'detalle', 'description'], null),
    peso: pick(e, ['peso', 'counts_toward_peso'], true) !== false,
  }
}

export function normalizeMoneyTrailStep(s) {
  const from = toRef(pick(s, ['from', 'from_clabe', 'origen'], null))
  const to = toRef(pick(s, ['to', 'to_clabe', 'destino'], null))
  return {
    from: from ? from.ref : null,
    fromLabel: pick(s, ['from_label', 'fromLabel'], from ? from.label : null),
    to: to ? to.ref : null,
    toLabel: pick(s, ['to_label', 'toLabel'], to ? to.label : null),
    amount: num(pick(s, ['amount', 'monto', 'total'], null)),
    date: pick(s, ['date', 'fecha'], null),
    exhibitId: pick(s, ['exhibit_id', 'exhibitId', 'record_id', 'ref'], null),
    note: pick(s, ['note', 'nota', 'reference'], null),
    step: pick(s, ['step', 'hop'], null),
  }
}

export function reconcileFinding(exhibits, pesoAmount) {
  const byTable = {}
  for (const e of exhibits) {
    if (!e.sourceTable || !e.peso || e.amount == null) continue
    byTable[e.sourceTable] = byTable[e.sourceTable] || { count: 0, sum: 0 }
    byTable[e.sourceTable].count += 1
    byTable[e.sourceTable].sum += e.amount
  }
  const tables = Object.entries(byTable).map(([table, v]) => ({
    table,
    count: v.count,
    sum: Math.round(v.sum * 100) / 100,
  }))

  let best = null
  if (pesoAmount != null && pesoAmount > 0) {
    for (const t of tables) {
      const diff = Math.abs(t.sum - pesoAmount) / pesoAmount
      if (!best || diff < best.diff) best = { table: t.table, sum: t.sum, diff }
    }
    if (best) best.verdict = best.diff <= 0.02 ? 'ok' : 'fail'
  }
  return { tables, best }
}

export function normalizeFinding(f) {
  const exhibits = (pick(f, ['exhibits', 'evidencia', 'evidence'], []) || []).map(normalizeExhibit)
  const rawTrail = pick(f, ['money_trail', 'moneyTrail', 'trail'], []) || []
  const moneyTrail = rawTrail.map(normalizeMoneyTrailStep)

  const ch = pick(f, ['challenger', 'retador'], null)
  const peso = num(pick(f, ['peso_amount', 'pesoAmount', 'monto', 'amount'], null))

  return {
    id: pick(f, ['id', 'finding_id', 'scheme_id'], null),
    schemeType: pick(f, ['scheme_type', 'schemeType', 'type'], null),
    severity: pick(f, ['severity', 'difficulty', 'confidence'], null),
    entities: pick(f, ['entities'], []) || [],
    pesoAmount: peso,
    returnPct: num(pick(f, ['return_pct', 'returnPct'], null)),
    narrative: pick(f, ['narrative', 'narracion', 'resumen'], null),
    challenger: ch
      ? {
          survives: pick(ch, ['survives', 'sobrevive'], true) !== false,
          argument: pick(ch, ['argument', 'argumento', 'explanation', 'argumento_inocente'], null),
          whyNotEnough: pick(ch, ['why_not_enough', 'whyNotEnough', 'contraargumento', 'por_que_no_basto'], null),
        }
      : null,
    exhibits,
    moneyTrail,
    reconcile: reconcileFinding(exhibits, peso),
  }
}

export function normalizeLead(l) {
  return {
    entity: pick(l, ['entity', 'rfc'], null),
    entityLabel: pick(l, ['entity_label', 'entityLabel', 'nombre', 'name', 'legal_name'], null),
    signal: pick(l, ['signal', 'senal', 'detector'], null),
    reason: pick(l, ['reason', 'motivo', 'razon', 'why'], null),
    toolCallsMade: pick(l, ['tool_calls_made', 'toolCallsMade', 'tools'], []) || [],
    closedBy: pick(l, ['closed_by', 'closedBy'], null),
  }
}

export function normalizeSubmission(raw) {
  if (!raw || typeof raw !== 'object') throw new Error('El archivo no es un submission.json válido')

  const runMeta = pick(raw, ['run_metadata', 'runMetadata', 'metadata'], {}) || {}
  return {
    seed: num(pick(raw, ['seed', 'run'] , null)),
    companyRfc: pick(raw, ['company_rfc', 'companyRfc', 'company'], null),
    companyLabel: pick(raw, ['company_label', 'companyLabel', 'empresa'], null),
    period: pick(raw, ['period', 'periodo'], null),
    run: {
      llmCalls: num(pick(runMeta, ['llm_calls', 'llmCalls'], null)),
      mxnCost: num(pick(runMeta, ['mxn_cost', 'mxnCost'], null)),
      wallClockSeconds: num(pick(runMeta, ['wall_clock_seconds', 'wallClockSeconds'], null)),
      deterministic: pick(runMeta, ['deterministic', 'determinista'], null),
      model: pick(runMeta, ['model', 'modelo'], null),
    },
    findings: (pick(raw, ['findings', 'hallazgos', 'acusaciones'], []) || []).map(normalizeFinding),
    leads: (pick(raw, ['leads_not_pursued', 'leads', 'descartados'], []) || []).map(normalizeLead),
  }
}