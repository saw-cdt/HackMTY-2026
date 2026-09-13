import { useMemo, useState } from 'react'
import Sidebar from './components/Sidebar'
import ThemeToggle from './components/ThemeToggle'
import LanguageToggle from './components/LanguageToggle'
import DropZone from './components/DropZone'
import GraphView from './components/GraphView'
import StatCards from './components/StatCards'
import ContrastPanel from './components/ContrastPanel'
import LeadsList from './components/LeadsList'
import NodeDetailDrawer from './components/NodeDetailDrawer'
import { useTheme } from './hooks/useTheme'
import { useLanguage } from './hooks/useLanguage'
import { useProgressiveSteps } from './hooks/useProgressiveSteps'
import { adaptSubmission } from './data/adaptUi'
import { t } from './i18n/strings'

const DEMO_JSON_PATH = `${import.meta.env.BASE_URL}demo/submission_seed004.json`

function companionSubmissionName(dbFileName) {
  return dbFileName.replace(/^estate_/, 'submission_').replace(/\.db$/i, '.json')
}

export default function App() {
  const { isDark, toggle } = useTheme()
  const { lang, toggle: toggleLang } = useLanguage()
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
        if (!res.ok) throw new Error(t(lang, 'errNoSubmissionFor', file.name))
        json = await res.json()
      } else {
        throw new Error(t(lang, 'errDropDbOrJson'))
      }
      loadSubmission(json)
    } catch (err) {
      setError(err.message || t(lang, 'errCouldNotRead'))
    }
  }

  const handleLoadDemo = async () => {
    setError(null)
    try {
      const res = await fetch(DEMO_JSON_PATH)
      if (!res.ok) throw new Error(t(lang, 'errNoDemoFound'))
      loadSubmission(await res.json())
    } catch (err) {
      setError(err.message || t(lang, 'errCouldNotLoadDemo'))
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
        lang={lang}
        onToggleLang={toggleLang}
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
        lang={lang}
      />

      <div className="main">
        <div className="topbar">
          <div>
            <h1>{view === 'leads' ? t(lang, 'leadsTitle') : model.companyLabel}</h1>
            <div className="topbar-meta">
              {view === 'leads'
                ? t(lang, 'leadsAvailableNote')
                : `${model.companyRfc} · ${model.period}`}
            </div>
          </div>
          <div className="topbar-right">
            {appState === 'running' && view === 'audit' && (
              <button type="button" className="btn btn-ghost" onClick={skip}>
                {t(lang, 'skipAnimation')}
              </button>
            )}
            <LanguageToggle lang={lang} onToggle={toggleLang} />
            <ThemeToggle isDark={isDark} onToggle={toggle} />
          </div>
        </div>

        <div className="content">
          {view === 'leads' ? (
            <LeadsList leads={model.leadsNotPursued} lang={lang} />
          ) : (
            <>
              {appState === 'running' && (
                <div className="running-banner">
                  <span className="pulse-dot" />
                  {t(lang, 'runningBanner', step, model.maxStep)}
                </div>
              )}

              <GraphView
                model={model}
                step={appState === 'running' ? step : model.maxStep}
                onSelectNode={setSelectedNodeId}
                selectedId={selectedNodeId}
                lang={lang}
              />

              {appState === 'result' && (
                <>
                  <StatCards runMetadata={model.runMetadata} lang={lang} />
                  <ContrastPanel model={model} lang={lang} />
                </>
              )}
            </>
          )}
        </div>
      </div>

      <NodeDetailDrawer
        node={selectedNode}
        ctx={selectedCtx}
        onClose={() => setSelectedNodeId(null)}
        lang={lang}
      />
    </div>
  )
}
