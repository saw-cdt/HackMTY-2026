import { schemeMeta } from '../lib/schemes.js'
import { fmtMXN, fmtSec } from '../lib/format.js'

export default function ResultsTab({ submissions, survey }) {
  const bySeed = {}
  for (const s of submissions) {
    bySeed[String(s.seed)] = s
  }

  const surveySeeds = survey ? Object.entries(survey.rows || {}) : []
  const extraSeeds = submissions
    .filter((s) => s.seed != null && !surveySeeds.some(([k]) => k === String(s.seed)))
    .map((s) => [
      String(s.seed),
      { seed: s.seed, n_schemes: null, n_decoys: null, scheme_types: {}, peso_sembrado: null, company_rfc: null },
    ])

  const allRows = [...surveySeeds, ...extraSeeds]
  const foundTotals = { schemes: 0, decoys: 0 }
  const plantedTotals = { schemes: 0 }

  for (const [seed] of allRows) {
    const sub = bySeed[seed]
    foundTotals.schemes += sub?.findings?.length || 0
    foundTotals.decoys += sub?.leads?.length || 0
    const s = survey?.rows?.[seed]
    if (s) plantedTotals.schemes += s.n_schemes || 0
  }

  return (
    <div>
      <div className="note-box" style={{ marginBottom: 16 }}>
        <div className="hd">Seeds de instrucción 1–10 · de reporte 101–110</div>
        Lo sembrado sale de <span className="mono">truth_seedNNN.json</span> (lo que el agente nunca abre). Lo encontrado, de cada <span className="mono">submission_seedNNN.json</span> que cargues. Cargando más submissions, la tabla se llena sola.
      </div>

      <div className="grid grid-4" style={{ marginBottom: 16 }}>
        <div className="stat-pill"><div className="v">{allRows.length}</div><div className="k">seeds en tabla</div></div>
        <div className="stat-pill"><div className="v primary">{plantedTotals.schemes || 0}</div><div className="k">esquemas sembrados</div></div>
        <div className="stat-pill"><div className="v ok">{foundTotals.schemes}</div><div className="k">esquemas encontrados</div></div>
        <div className="stat-pill"><div className="v danger">{foundTotals.decoys}</div><div className="k">leads descartados</div></div>
      </div>

      <div className="card flat nopad">
        <div className="tbl-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Seed</th>
                <th>Empresa</th>
                <th>Sembrado</th>
                <th>Encontrado</th>
                <th style={{ textAlign: 'right' }}>Exposición</th>
                <th style={{ textAlign: 'right' }}>llm_calls</th>
                <th style={{ textAlign: 'right' }}>mxn_cost</th>
                <th style={{ textAlign: 'right' }}>wall_clock</th>
              </tr>
            </thead>
            <tbody>
              {allRows.map(([seed, row]) => {
                const s = row
                const sub = bySeed[seed]
                const findings = sub?.findings || []
                const leads = sub?.leads || []
                const exposure = findings.reduce((a, f) => a + (f.pesoAmount || 0), 0)
                const run = sub?.run || {}
                return (
                  <tr key={seed}>
                    <td className="key">{seed}</td>
                    <td className="mono">{s.company_rfc || sub?.companyRfc || '—'}</td>
                    <td>
                      <span className="chip chip-warn">
                        {s.n_schemes == null ? '—' : s.n_schemes} esquemas
                      </span>
                      {s.n_decoys != null && (
                        <span className="chip">{(s.n_schemes == null ? 0 : s.n_decoys)} decoys</span>
                      )}
                      {s.scheme_types && Object.entries(s.scheme_types).length > 0 && (
                        <div className="faint mono" style={{ fontSize: 10.5, marginTop: 4 }}>
                          {Object.entries(s.scheme_types).map(([t, n]) => `${schemeMeta(t).label} ×${n}`).join(' · ')}
                        </div>
                      )}
                    </td>
                    <td>
                      {sub ? (
                        <>
                          <span className="chip chip-ok">
                            {findings.length} hallazgos
                          </span>
                          <span className="chip">{leads.length} leads</span>
                        </>
                      ) : (
                        <span className="faint mono">sin submission cargado</span>
                      )}
                    </td>
                    <td className="amt">{sub && exposure > 0 ? fmtMXN(exposure) : '—'}</td>
                    <td className="amt mono">{sub ? run.llmCalls ?? '—' : '—'}</td>
                    <td className="amt mono">{sub ? (run.mxnCost === 0 ? '0' : run.mxnCost ?? '—') : '—'}</td>
                    <td className="amt mono">{sub ? fmtSec(run.wallClockSeconds) : '—'}</td>
                  </tr>
                )
              })}
              {allRows.length === 0 && (
                <tr>
                  <td colSpan={8} className="empty">Carga seeds para tener una tabla real.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="section-head" style={{ marginTop: 30 }}>
        <span className="no">IV</span>
        <h2>Método y límites</h2>
        <span className="kicker">qué se declara, qué no se promete</span>
      </div>
      <div className="grid grid-2">
        <div className="card flat">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 16, marginTop: 0 }}>Qué sistema hace</h3>
          <ul style={{ margin: 0, paddingLeft: 18, color: 'var(--text)' }}>
            <li>Ningún hallazgo se imprime sin retador y validador.</li>
            <li>Los montos se computan con SQL contra el estate, nunca por el modelo.</li>
            <li>Cada lead descartado registra quién lo cerró y la razón con evidencia citada.</li>
            <li>El mismo seed reproduce el mismo caso (temperatura 0 + caché sha256).</li>
            <li>El ground truth vive aparte y el agente no lo importa (grep en el build).</li>
          </ul>
        </div>
        <div className="card flat">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 16, marginTop: 0 }}>Qué sistema no detecta</h3>
          <ul style={{ margin: 0, paddingLeft: 18, color: 'var(--text)' }}>
            <li>Esquemas entrelazados: no se generan en nuestro conjunto de prueba; el sistema los procesa pero no está afinado para ellos.</li>
            <li>Fraude fuera de los cinco esquemas del formato oficial.</li>
            <li>Operaciones en efectivo sin huella bancaria en <span className="mono">bank_txns</span>.</li>
            <li>Colusión por fuera del estate: el detector solo ve lo que las 8 tablas documentan.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
