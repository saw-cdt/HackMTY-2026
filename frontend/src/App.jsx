import { useState, useEffect } from 'react'
import { Search, ShieldAlert, CheckCircle2 } from 'lucide-react'
import DropZone from './components/DropZone.jsx'
import SummaryTab from './components/SummaryTab.jsx'
import FindingCard from './components/FindingCard.jsx'
import ContrastView from './components/ContrastView.jsx'
import LeadsTable from './components/LeadsTable.jsx'
import CaseGraph from './components/CaseGraph.jsx'
import EstatePanel from './components/EstatePanel.jsx'
import ResultsTab from './components/ResultsTab.jsx'
import { normalizeSubmission } from './lib/normalize.js'
import { parseEstateFile, parseEstateBuf } from './lib/estate.js'
import { PIPELINE } from './lib/schemes.js'

const TABS = [
  { id: 'resumen', label: 'Resumen' },
  { id: 'hallazgos', label: 'Hallazgos' },
  { id: 'contraste', label: 'Contraste' },
  { id: 'leads', label: 'Leads' },
  { id: 'grafo', label: 'Grafo' },
  { id: 'estate', label: 'Estate' },
  { id: 'resultados', label: 'Resultados' },
]

export default function App() {
  const [submission, setSubmission] = useState(null)
  const [estate, setEstate] = useState(null)
  const [survey, setSurvey] = useState(null)
  const [submissionList, setSubmissionList] = useState([])
  const [tab, setTab] = useState('resumen')
  const [loading, setLoading] = useState(false)
  const [banner, setBanner] = useState(null)
  const [fileName, setFileName] = useState({ sub: null, db: null })

  useEffect(() => {
    fetch('/demo/truth_survey.json')
      .then((r) => r.json())
      .then(setSurvey)
      .catch(() => {})
  }, [])

  const flash = (msg) => {
    setBanner(msg)
    window.setTimeout(() => setBanner(null), 6000)
  }

  async function handleSubmissionFile(file) {
    setLoading(true)
    try {
      const text = await file.text()
      const raw = JSON.parse(text)
      const sub = normalizeSubmission(raw)
      if (!sub.findings.length && !sub.leads.length) {
        flash('El submission no trae findings ni leads; ¿es el formato oficial?')
      }
      setFileName((f) => ({ ...f, sub: file.name }))
      setSubmission(sub)
      setSubmissionList((list) => {
        const next = list.filter((s) => s.seed !== sub.seed)
        return [...next, sub]
      })
      setTab('resumen')
      flash(`Cargado ${file.name} · ${sub.findings.length} hallazgos · ${sub.leads.length} leads`)
    } catch (e) {
      flash(`No pude leer ${file.name}: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleEstateFile(file) {
    setLoading(true)
    try {
      const est = await parseEstateFile(file)
      est.fileName = file.name
      setFileName((f) => ({ ...f, db: file.name }))
      setEstate(est)
      flash(`Estate cargado · ${est.counts.vendors} proveedores · ${est.counts.invoices} facturas`)
      if (!submission) setTab('estate')
    } catch (e) {
      flash(`No pude abrir el estate: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  async function loadDemo() {
    setLoading(true)
    try {
      const subRes = await fetch('/demo/submission_seed004.json')
      const raw = await subRes.json()
      const sub = normalizeSubmission(raw)
      setSubmission(sub)
      setSubmissionList([sub])
      setFileName((f) => ({ ...f, sub: 'demo/submission_seed004.json' }))

      const dbRes = await fetch('/demo/estate_seed004.db')
      const est = await parseEstateBuf(await dbRes.arrayBuffer())
      est.fileName = 'demo/estate_seed004.db'
      setEstate(est)
      setFileName((f) => ({ ...f, db: 'demo/estate_seed004.db' }))

      setTab('resumen')
      flash('Demo de seed 004 cargado: estate + submission reales del generador.')
    } catch (e) {
      flash(`No pude cargar la demo: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const hasContent = Boolean(submission || estate)

  return (
    <div>
      <header className="masthead">
        <div className="rule" />
        <div className="masthead-inner">
          <div className="brand">
            <div className="seal">FA</div>
            <div>
              <h1>The Forensic Auditor</h1>
              <div className="sub">HackMTY 2026 · Infosys · expediente de fraude fiscal</div>
            </div>
          </div>
          <div className="loaded-tag">
            {fileName.sub && <span className="file-badge"><span className="dot" />{fileName.sub}</span>}
            {fileName.db && <span className="file-badge"><span className="dot" />{fileName.db}</span>}
            <button className="btn btn-primary" onClick={loadDemo} disabled={loading}>
              Cargar demo
            </button>
          </div>
        </div>
        <nav className="tabs">
          {TABS.map((t) => (
            <button key={t.id} className={`tab${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
              <span className="idx">{String(TABS.indexOf(t) + 1).padStart(2, '0')}</span>
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="page">
        {banner && <div className="note-box toast-bar"><div className="hd">Sistema</div>{banner}</div>}

        {!hasContent ? (
          <Landing onSubmission={handleSubmissionFile} onEstate={handleEstateFile} loading={loading} onDemo={loadDemo} />
        ) : (
          <>
            {tab === 'resumen' && (
              submission ? <SummaryTab submission={submission} estate={estate} /> : <EstatePanel estate={estate} />
            )}

            {tab === 'hallazgos' &&
              (submission?.findings?.length ? (
                submission.findings.map((f) => <FindingCard key={f.id || f.schemeType} finding={f} estate={estate} />)
              ) : (
                <div className="empty">
                  No hay hallazgos publicados.
                  <div className="mono">Si el estate no tiene fraude, la lista vacía es el resultado correcto.</div>
                </div>
              ))}

            {tab === 'contraste' && submission && <ContrastView submission={submission} />}

            {tab === 'leads' &&
              (submission?.leads?.length ? (
                <LeadsTable leads={submission.leads} />
              ) : (
                <div className="empty">Sin leads descartados en este informe.</div>
              ))}

            {tab === 'grafo' &&
              (submission ? <CaseGraph submission={submission} estate={estate} /> : <div className="empty">Carga un submission para ver el grafo del caso.</div>)}

            {tab === 'estate' && <EstatePanel estate={estate} />}

            {tab === 'resultados' && <ResultsTab submissions={submissionList} survey={survey} />}
          </>
        )}
      </main>
    </div>
  )
}

function Landing({ onSubmission, onEstate, loading, onDemo }) {
  return (
    <div>
      <div className="hero">
        <div className="eyebrow">El jurado suelta un estate · el agente investiga · el retador tumba · el validador verifica</div>
        <h2>Ningún hallazgo se imprime sin haber sido atacado.</h2>
        <p>
          Investigador arma. Retador intenta tumbarlo con la explicación inocente más fuerte. Validador verifica en
          código que cada registro exista y que el monto reconcilie al 2%. Lo que sobrevive se publica con su prueba.
        </p>
      </div>

      <div className="pipeline">
        {PIPELINE.map((p) => {
          const Icon = { Search, ShieldAlert, CheckCircle2 }[p.icon]
          return (
            <div className="step" key={p.stage}>
              <span className="n">paso {p.stage}</span>
              <span className="r" style={{ color: p.color }}>
                {Icon && <Icon size={14} aria-hidden="true" />} {p.role}
              </span>
              <span className="v">{p.verb}</span>
            </div>
          )
        })}
      </div>

      <div className="dropzone-wrap" style={{ marginTop: 34 }}>
        <DropZone onSubmission={onSubmission} onEstate={onEstate} loading={loading} />
      </div>

      <div className="demo-links">
        <button className="btn btn-primary" onClick={onDemo} disabled={loading}>
          Abrir demo — seed 004 (estate real + informe real)
        </button>
      </div>

      <div className="quote">
        «Lo que un sistema descarta dice tanto como lo que acusa. Acusar a un decoy pesa lo mismo en la métrica que
        perder un esquema.»
      </div>
    </div>
  )
}