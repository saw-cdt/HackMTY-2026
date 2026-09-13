import { useMemo, useState } from 'react'
import Sidebar from './components/Sidebar'
import ThemeToggle from './components/ThemeToggle'
import DropZone from './components/DropZone'
import GraphView from './components/GraphView'
import StatCards from './components/StatCards'
import ContrastPanel from './components/ContrastPanel'
import LeadsList from './components/LeadsList'
import NodeDetailDrawer from './components/NodeDetailDrawer'
import { useTheme } from './hooks/useTheme'
import { useProgressiveSteps } from './hooks/useProgressiveSteps'
import { adaptSubmission } from './data/adaptUi'

const DEMO_JSON_PATH = `${import.meta.env.BASE_URL}demo/submission_seed004.json`

function companionSubmissionName(dbFileName) {
  return dbFileName.replace(/^estate_/, 'submission_').replace(/\.db$/i, '.json')
}

export default function App() {
  const { isDark, toggle } = useTheme()
  const [submission, setSubmission] = useState(null)
  const [error, setError] = useState(null)
  const [appState, setAppState] = useState('idle') // idle | running | result
  const [view, setView] = useState('audit') // audit | leads
  const [selectedNodeId, setSelectedNodeId] = useState(null)

  const model = useMemo(() => (submission ? adaptSubmission(submission) : null), [submission])

  const { step, skip } = useProgressiveSteps(model?.maxStep || 6, {
    active: appState === 'running',
    onDone: () => setAppState('result'),
  })

  const loadSubmission = (json) => {
    setSubmission(json)
    setAppState('running')
    setView('audit')
    setSelectedNodeId(null)
    setError(null)
  }

  const handleFile = async (file) => {
    setError(null)
    try {
      let json
      if (file.name.toLowerCase().endsWith('.json')) {
        json = JSON.parse(await file.text())
      } else if (file.name.toLowerCase().endsWith('.db')) {
        const url = `${import.meta.env.BASE_URL}demo/${companionSubmissionName(file.name)}`
        const res = await fetch(url)
        if (!res.ok) throw new Error(`No hay submission.json preparado para ${file.name}.`)
        json = await res.json()
      } else {
        throw new Error('Suelta un archivo .db o un submission.json.')
      }
      loadSubmission(json)
    } catch (err) {
      setError(err.message || 'No se pudo leer el archivo.')
    }
  }

  const handleLoadDemo = async () => {
    setError(null)
    try {
      const res = await fetch(DEMO_JSON_PATH)
      if (!res.ok) throw new Error('No se encontró el submission.json de demo.')
      loadSubmission(await res.json())
    } catch (err) {
      setError(err.message || 'No se pudo cargar la demo.')
    }
  }

  const handleReset = () => {
    setSubmission(null)
    setAppState('idle')
    setView('audit')
    setSelectedNodeId(null)
    setError(null)
  }

  if (!submission || !model) {
    return (
      <DropZone
        onFile={handleFile}
        onLoadDemo={handleLoadDemo}
        error={error}
        isDark={isDark}
        onToggleTheme={toggle}
      />
    )
  }

  const selectedNode = selectedNodeId ? model.nodes.find((n) => n.id === selectedNodeId) : null
  const selectedCtx = selectedNodeId ? model.getContext(selectedNodeId) : null

  return (
    <div className="app-shell">
      <Sidebar
        view={view}
        onNavigate={setView}
        appState={appState}
        onReset={handleReset}
        leadsCount={model.leadsNotPursued.length}
      />

      <div className="main">
        <div className="topbar">
          <div>
            <h1>{view === 'leads' ? 'Leads descartados' : model.companyLabel}</h1>
            <div className="topbar-meta">
              {view === 'leads'
                ? 'Disponible para la pregunta sorpresa del jurado'
                : `${model.companyRfc} · ${model.period}`}
            </div>
          </div>
          <div className="topbar-right">
            {appState === 'running' && view === 'audit' && (
              <button type="button" className="btn btn-ghost" onClick={skip}>
                Saltar animación
              </button>
            )}
            <ThemeToggle isDark={isDark} onToggle={toggle} />
          </div>
        </div>

        <div className="content">
          {view === 'leads' ? (
            <LeadsList leads={model.leadsNotPursued} />
          ) : (
            <>
              {appState === 'running' && (
                <div className="running-banner">
                  <span className="pulse-dot" />
                  Reconstruyendo el rastro del dinero — paso {step} de {model.maxStep}
                </div>
              )}

              <GraphView
                model={model}
                step={appState === 'running' ? step : model.maxStep}
                onSelectNode={setSelectedNodeId}
                selectedId={selectedNodeId}
              />

              {appState === 'result' && (
                <>
                  <StatCards runMetadata={model.runMetadata} />
                  <ContrastPanel model={model} />
                </>
              )}
            </>
          )}
        </div>
      </div>

      <NodeDetailDrawer node={selectedNode} ctx={selectedCtx} onClose={() => setSelectedNodeId(null)} />
    </div>
  )
}
