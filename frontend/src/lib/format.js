export const fmtMXN = (v) =>
  v == null
    ? '—'
    : new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        maximumFractionDigits: 0,
      }).format(v)

export const fmtMXNexact = (v) =>
  v == null
    ? '—'
    : new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(v)

export const fmtNum = (v) =>
  v == null ? '—' : new Intl.NumberFormat('es-MX').format(v)

export const fmtDate = (d) => {
  if (!d) return '—'
  const dt = new Date(d)
  if (Number.isNaN(dt.getTime())) return d
  return dt.toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export const fmtPct = (v, digits = 1) =>
  v == null ? '—' : `${v.toFixed(digits)}%`

export const fmtSec = (v) =>
  v == null ? '—' : `${Number(v).toFixed(1)} s`

export const shortClabe = (c) =>
  c ? `CLABE ····${c.slice(Math.max(0, c.length - 4))}` : ''

export const shortRfc = (r) => (r || '').replace(/^RFC:/i, '')