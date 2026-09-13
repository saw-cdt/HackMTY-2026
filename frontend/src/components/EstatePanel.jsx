import { AlertTriangle } from 'lucide-react'
import { fmtNum } from '../lib/format.js'

const TABLE_NAMES = {
  vendors: 'Proveedores',
  invoices: 'Facturas CFDI',
  ledger: 'Asientos contables',
  bank_txns: 'Transferencias',
  purchase_orders: 'Órdenes de compra',
  contracts: 'Contratos',
  employees: 'Empleados',
  efos_list: 'Lista 69-B',
}

export default function EstatePanel({ estate }) {
  if (!estate) return <div className="empty">Suelta un <span className="mono">estate_seedNNN.db</span> para inspeccionarlo.</div>

  return (
    <div>
      {estate.missing.length > 0 && (
        <div className="note-box note-box-danger">
          <div className="hd"><AlertTriangle size={12} aria-hidden="true" /> No es un estate del formato oficial</div>
          Faltan {estate.missing.join(', ')} de las 8 tablas. Los jueces leen los nombres de columna directo del schema.
        </div>
      )}

      <div className="grid grid-4">
        {Object.entries(TABLE_NAMES).map(([key, label]) => {
          const n = estate.counts?.[key] ?? 0
          const missing = estate.missing?.includes(key)
          return (
            <div className="stat-pill" key={key} style={missing ? { borderColor: 'var(--danger)' } : {}}>
              <div className="v" style={missing ? { color: 'var(--danger)' } : {}}>{fmtNum(n)}</div>
              <div className="k">{label}</div>
              <div className="faint mono" style={{ fontSize: 10, marginTop: 2 }}>{key}</div>
            </div>
          )
        })}
        <div className="stat-pill" style={{ borderColor: 'var(--violet-300)' }}>
          <div className="v primary">{estate.companyClabes?.length || 0}</div>
          <div className="k">CLABE(s) de la empresa</div>
        </div>
        <div className="stat-pill">
          <div className="v danger">{estate.efosStatus?.definitivo || 0}</div>
          <div className="k">69-B definitivo</div>
        </div>
        <div className="stat-pill">
          <div className="v" style={{ color: 'var(--warn)' }}>{estate.efosStatus?.presunto || 0}</div>
          <div className="k">69-B presunto</div>
        </div>
      </div>

      <div className="section-head">
        <span className="no">E</span>
        <h2>Proveedores del estate</h2>
        <span className="kicker">{estate.vendors.length} en vendors</span>
      </div>

      <div className="card flat nopad">
        <div className="tbl-scroll" style={{ maxHeight: 480, overflowY: 'auto' }}>
          <table className="data-table">
            <thead style={{ position: 'sticky', top: 0, background: 'var(--surface-2)', zIndex: 1 }}>
              <tr>
                <th>RFC</th>
                <th>Razón social</th>
                <th>Categoría</th>
                <th>Alta</th>
                <th>CLABE</th>
                <th>69-B</th>
              </tr>
            </thead>
            <tbody>
              {estate.vendors.map((v) => {
                const ef = estate.efosByRfc?.[v.rfc]
                return (
                  <tr key={v.rfc}>
                    <td className="key">{v.rfc}</td>
                    <td>{v.legal_name}</td>
                    <td className="muted">{v.category}</td>
                    <td className="mono">{v.registered_date}</td>
                    <td className="mono faint">{v.bank_clabe}</td>
                    <td>
                      {ef ? (
                        <span className={`chip ${ef === 'definitivo' ? 'chip-danger' : 'chip-warn'}`}>
                          {ef}
                        </span>
                      ) : (
                        <span className="faint">—</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
