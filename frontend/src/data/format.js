export function formatMxn(value) {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatNumber(value) {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('es-MX').format(value)
}

export function formatSeconds(value) {
  if (value === null || value === undefined) return '—'
  return `${new Intl.NumberFormat('es-MX', { maximumFractionDigits: 1 }).format(value)} s`
}

export function formatDate(value) {
  if (!value) return '—'
  return value
}

export const STATE_LABEL = {
  neutral: 'Sin evaluar',
  dismissed: 'Descartado',
  flagged: 'Candidato',
  accused: 'Hallazgo',
}
