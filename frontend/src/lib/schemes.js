// Paleta y metadatos de dominio. Los colores salen de DESIGN.md:
// - SCHEME_META usa la paleta categórica validada del §8.1 (orden fijo,
//   nunca se cicla ni se reordena — el color sigue a la entidad).
// - CLOSED_BY_META usa los tokens semánticos del §3.5, mapeados 1:1 a la
//   columna "Significado en la app" de esa tabla: investigator -> Descartado
//   (lead_not_pursued genérico), challenger -> Retado (explicación inocente
//   en revisión), validator -> Crítico (falsa acusación / rechazo).

export const SCHEME_META = {
  phantom_vendor: {
    label: 'Proveedor fantasma',
    color: 'var(--series-1)',
    colorHex: '#5B4BE1',
    soft: 'color-mix(in oklab, var(--series-1) 12%, var(--slate-50))',
    rule: 'Proveedor que no existe u opera: factura servicios que nunca prestó.',
    detect: 'Cruce con lista 69-B + ausencia de contrato y orden de compra.',
  },
  kickback: {
    label: 'Comisión encubierta',
    color: 'var(--series-2)',
    colorHex: '#0E9F8B',
    soft: 'color-mix(in oklab, var(--series-2) 12%, var(--slate-50))',
    rule: 'El proveedor devuelve parte del pago a un empleado de la empresa.',
    detect: 'Transferencias de un proveedor a un CLABE de empleado.',
  },
  round_tripping: {
    label: 'Ciclo de retorno',
    color: 'var(--series-3)',
    colorHex: '#B57209',
    soft: 'color-mix(in oklab, var(--series-3) 12%, var(--slate-50))',
    rule: 'El dinero sale y regresa a la propia empresa dando la vuelta.',
    detect: 'Recorrido recursivo sobre bank_txns que cierra en el CLABE de la empresa.',
  },
  threshold_splitting: {
    label: 'Fraccionamiento de umbral',
    color: 'var(--series-4)',
    colorHex: '#2E90D9',
    soft: 'color-mix(in oklab, var(--series-4) 12%, var(--slate-50))',
    rule: 'Facturas partidas para quedar bajo el límite de aprobación.',
    detect: 'Agrupación por proveedor y ventana de fechas contra el umbral inferido.',
  },
  revenue_inflation: {
    label: 'Inflación de ingresos',
    color: 'var(--series-5)',
    colorHex: '#C4423B',
    soft: 'color-mix(in oklab, var(--series-5) 12%, var(--slate-50))',
    rule: 'La empresa emite facturas por ventas que nunca ocurrieron.',
    detect: 'Facturas emitidas por la empresa sin bank_txn que las liquide.',
  },
}

export const schemeMeta = (t) => SCHEME_META[t] || {
  label: t,
  color: 'var(--neutral)',
  colorHex: '#6B75A0',
  soft: 'color-mix(in oklab, var(--neutral) 12%, var(--slate-50))',
  rule: '',
  detect: '',
}

// Los tres valores que acepta closed_by en el formato oficial, mapeados a
// los tokens semánticos de DESIGN.md §3.5. "icon" es el nombre del ícono de
// lucide-react que exige la regla "todo estado lleva icono + etiqueta".
export const CLOSED_BY_META = {
  investigator: {
    label: 'Descartado',
    who: 'El investigador descartó el candidato al examinar la evidencia.',
    color: 'var(--neutral)',
    soft: 'var(--tint-neutral)',
    icon: 'Archive',
  },
  challenger: {
    label: 'Retado',
    who: 'El retador lo tumbó con la explicación inocente más fuerte.',
    color: 'var(--warn)',
    soft: 'var(--tint-warn)',
    icon: 'ShieldAlert',
  },
  validator: {
    label: 'Crítico',
    who: 'El validador en código lo rechazó: cita, monto o trail no pasan.',
    color: 'var(--danger)',
    soft: 'var(--tint-danger)',
    icon: 'AlertOctagon',
  },
}

export const closedByMeta = (k) => CLOSED_BY_META[k] || {
  label: k || '—',
  who: '',
  color: 'var(--neutral)',
  soft: 'var(--tint-neutral)',
  icon: 'HelpCircle',
}

// Las tres capas del pipeline — narrativa del demo. Colores semánticos:
// investigador construye (informativo), retador ataca (alerta), validador
// verifica en código (confirma o rechaza).
export const PIPELINE = [
  { stage: '01', role: 'Investigador', verb: 'arma el hallazgo · hipótesis + evidencia', color: 'var(--info)', icon: 'Search' },
  { stage: '02', role: 'Retador', verb: 'intenta tumbarlo · la explicación inocente más fuerte', color: 'var(--warn)', icon: 'ShieldAlert' },
  { stage: '03', role: 'Validador', verb: 'verifica en código · cita, reconcilia al 2%, cuenta', color: 'var(--ok)', icon: 'CheckCircle2' },
]
