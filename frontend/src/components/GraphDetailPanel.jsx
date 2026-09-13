import { fmtMXNexact, fmtDate, shortRfc } from '../lib/format.js'

// Panel de "a quién pertenece esta cuenta, qué la respalda, por qué se
// señaló" al hacer clic en un nodo o un monto del grafo. Es la pieza que
// tenía el prototipo de storyboard (Forensic Auditor Demo.dc.html) y que le
// faltaba a esta app real: ahí la resolvía con datos inventados a mano,
// aquí se resuelve contra el estate .db real que se cargó.
//
// Responde exactamente lo que las reglas piden poder contestar en menos de
// diez segundos: "¿por qué está aquí esta entidad?".

function vendorFacts(rfc, estate) {
  const v = estate?.vendors?.find((x) => x.rfc === rfc)
  const efosStatus = estate?.efosByRfc?.[rfc]
  const facts = []
  if (v) {
    facts.push(['Razón social', v.legal_name])
    facts.push(['Categoría', v.category || '—'])
    facts.push(['Alta', v.registered_date || '—'])
    facts.push(['CLABE', v.bank_clabe || '—'])
  }
  facts.push(['Estatus 69-B', efosStatus || 'sin registro en efos_list'])
  if (!v) facts.push(['Nota', 'No aparece en vendors del estate cargado — no se puede verificar más.'])
  return facts
}

function employeeFacts(id, estate) {
  const e = estate?.employees?.find((x) => `EMP:${x.emp_id}` === id)
  if (!e) return [['Nota', 'No aparece en employees del estate cargado — no se puede verificar más.']]
  return [
    ['Nombre', e.name],
    ['Rol', e.role || '—'],
    ['Contratación', e.hire_date || '—'],
    ['CLABE', e.bank_clabe || '—'],
  ]
}

function clabeFacts(clabe) {
  return [
    ['CLABE completa', clabe || '—'],
    ['Banco (3 primeros dígitos)', clabe ? clabe.slice(0, 3) : '—'],
    ['Nota', 'No coincide con ningún bank_clabe de vendors ni employees en el estate cargado.'],
  ]
}

function nodeDetail(node, estate) {
  if (node.kind === 'company') {
    return {
      title: node.label || 'Empresa investigada',
      kind: 'Empresa auditada',
      prose:
        'Es la empresa cuyo estate se está auditando: aparece como receptora en las facturas y como origen en las transferencias que arman cada hallazgo. No se acusa a la empresa — se documenta qué salió de sus cuentas y hacia dónde.',
      facts: [['RFC', node.rfc ? shortRfc(node.rfc) : '—'], ['CLABE(s) de la empresa', estate?.companyClabes?.length ? estate.companyClabes.join(', ') : 'no resuelto (sin estate cargado)']],
    }
  }
  if (node.kind === 'employee') {
    return {
      title: node.label || node.id,
      kind: 'Empleado',
      prose: 'Su CLABE se comparó contra el destino de una transferencia usando los 18 dígitos completos, nunca por prefijo bancario — así se distingue "recibió el dinero" de "usa el mismo banco".',
      facts: employeeFacts(node.id, estate),
    }
  }
  if (node.kind === 'clabe') {
    return {
      title: node.label || node.id,
      kind: 'Cuenta sin identidad resuelta',
      prose: 'Esta CLABE aparece en bank_txns pero no coincide con ningún proveedor ni empleado del estate cargado. Puede ser un intermediario fuera de las 8 tablas oficiales.',
      facts: clabeFacts(node.id),
    }
  }
  // entity (vendor) — RFC:...
  return {
    title: node.label || node.id,
    kind: node.found === false ? 'Lead descartado' : 'Proveedor señalado',
    prose:
      node.found === false
        ? 'Este candidato disparó un detector, pero al examinarlo el investigador (o el retador) encontró una explicación que se sostiene y cerró el lead. Ver la pestaña Leads para la razón exacta citada.'
        : 'Este proveedor forma parte de un hallazgo publicado: sobrevivió al retador y pasó la verificación del validador.',
    facts: vendorFacts(node.rfc || node.id, estate),
  }
}

function edgeDetail(edge, nodesById) {
  const from = nodesById[edge.from]
  const to = nodesById[edge.to]
  return {
    title: edge.exhibitId ? `${edge.exhibitId} · ${fmtMXNexact(edge.amount)}` : fmtMXNexact(edge.amount),
    kind: 'Transferencia · exhibit',
    prose: edge.note || 'Un tramo del money trail: el destino de este paso es el origen del siguiente, tal como exige el validador al verificar que el trail conecta.',
    facts: [
      ['Monto', fmtMXNexact(edge.amount)],
      ['Fecha', fmtDate(edge.date)],
      ['Origen', from?.label || edge.from || '—'],
      ['Destino', to?.label || edge.to || '—'],
      ['Exhibit citado', edge.exhibitId || '—'],
    ],
  }
}

export default function GraphDetailPanel({ selection, estate, nodesById }) {
  if (!selection) {
    return (
      <div className="graph-detail empty-hint">
        Haz clic en un nodo o en un monto para ver a quién pertenece la cuenta, qué la respalda, y por qué el agente
        la señaló o la descartó.
      </div>
    )
  }

  const d = selection.kind === 'edge' ? edgeDetail(selection.data, nodesById || {}) : nodeDetail(selection.data, estate)

  return (
    <div className="graph-detail">
      <div className="graph-detail-head">
        <span className="chip">{d.kind}</span>
        <h4>{d.title}</h4>
      </div>
      {d.prose && <p className="graph-detail-prose">{d.prose}</p>}
      <div className="graph-detail-facts">
        {d.facts.map(([k, v]) => (
          <div className="fact" key={k}>
            <span className="k">{k}</span>
            <span className="v mono">{v}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
