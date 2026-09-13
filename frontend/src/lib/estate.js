import initSqlJs from 'sql.js'
import wasmUrl from 'sql.js/dist/sql-wasm.wasm?url'

let SQLPromise = null

export function sqlJs() {
  if (!SQLPromise) {
    SQLPromise = initSqlJs({ locateFile: () => wasmUrl })
  }
  return SQLPromise
}

export async function parseEstateBuf(buf) {
  const SQL = await sqlJs()
  const db = new SQL.Database(new Uint8Array(buf))
  return loadEstate(db)
}

export async function parseEstateFile(file) {
  const buf = await file.arrayBuffer()
  return parseEstateBuf(buf)
}

function loadEstate(db) {
  const count = (t) => {
    try {
      const r = db.exec(`SELECT COUNT(*) FROM ${t}`)
      return r[0] ? r[0].values[0][0] : 0
    } catch {
      return 0
    }
  }

  const rows = (sql) => {
    const r = db.exec(sql)
    if (!r[0]) return []
    const cols = r[0].columns
    return r[0].values.map((v) => Object.fromEntries(cols.map((c, i) => [c, v[i]])))
  }

  const vendors = rows('SELECT * FROM vendors')
  const employees = rows('SELECT * FROM employees')
  const efos = rows('SELECT * FROM efos_list')
  const txns = rows('SELECT from_clabe, to_clabe FROM bank_txns')
  const tables = ['vendors', 'invoices', 'ledger', 'bank_txns', 'purchase_orders', 'contracts', 'employees', 'efos_list']

  const vendorClabes = new Set(vendors.map((v) => v.bank_clabe))
  const empClabes = new Set(employees.map((e) => e.bank_clabe))
  const clabeIndex = {}

  for (const v of vendors) {
    clabeIndex[v.bank_clabe] = { kind: 'vendor', rfc: `RFC:${v.rfc}`, label: `${v.rfc} · ${v.legal_name}` }
  }
  for (const e of employees) {
    clabeIndex[e.bank_clabe] = { kind: 'employee', id: e.emp_id, label: `${e.emp_id} · ${e.name}` }
  }

  const companyClabes = [
    ...new Set([
      ...txns.map((t) => t.from_clabe),
      ...txns.map((t) => t.to_clabe),
    ]).values(),
  ].filter((c) => c && !vendorClabes.has(c) && !empClabes.has(c))

  for (const c of companyClabes) clabeIndex[c] = { kind: 'company', clabe: c, label: 'EMPRESA INVESTIGADA' }

  const efosStatus = { definitivo: 0, presunto: 0 }
  const efosByRfc = {}
  for (const e of efos) {
    efosStatus[e.status] = (efosStatus[e.status] || 0) + 1
    efosByRfc[e.rfc] = e.status
  }

  const nameByRfc = {}
  for (const v of vendors) {
    nameByRfc[`RFC:${v.rfc}`] = v.legal_name
    nameByRfc[v.rfc] = v.legal_name
  }

  const declared = rows("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
  const declaredTables = declared.map((d) => d.name)
  const missing = tables.filter((t) => !declaredTables.includes(t))

  return {
    db,
    fileName: null,
    counts: Object.fromEntries(tables.map((t) => [t, count(t)])),
    missing,
    vendors,
    employees,
    evendorClabes: [...vendorClabes],
    companyClabes,
    clabeIndex,
    nameByRfc,
    efosByRfc,
    efosStatus,
  }
}

const TABLE_KEY_COL = {
  invoices: 'uuid',
  bank_txns: 'txn_id',
  ledger: 'entry_id',
  purchase_orders: 'po_id',
  contracts: 'contract_id',
  employees: 'emp_id',
  vendors: 'rfc',
  efos_list: 'rfc',
}

export function exhibitPresence(estate, records) {
  const ids = [...new Set(records.filter(Boolean))]
  const found = new Set()
  if (!ids.length || !estate?.db) return { ids, found, missing: ids }
  try {
    const where = ids.map(() => '?').join(',')
    for (const [table, col] of Object.entries(TABLE_KEY_COL)) {
      let res
      try {
        res = estate.db.exec(`SELECT ${col} FROM ${table} WHERE ${col} IN (${where})`, ids)
      } catch {
        continue
      }
      if (res[0]) {
        for (const row of res[0].values) found.add(String(row[0]))
      }
    }
  } catch {
    return { ids, found, missing: ids }
  }
  const missing = ids.filter((id) => !found.has(id))
  return { ids, found, missing }
}

export function analyseEstateForSubmission(estate, submission) {
  const records = []
  for (const f of submission.findings || []) {
    for (const e of f.exhibits || []) if (e.recordId) records.push(e.recordId)
    for (const s of f.moneyTrail || []) if (s.exhibitId) records.push(s.exhibitId)
  }
  const { found, missing, ids } = exhibitPresence(estate, records)
  return { cited: ids, found: found.size, missing: missing.length }
}