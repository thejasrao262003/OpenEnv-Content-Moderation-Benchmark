import { useState, useEffect } from 'react'
import ScenarioExplorer from './pages/ScenarioExplorer'
import AnalysisView from './pages/AnalysisView'
import { runAgent, getState, getHealth } from './api'
import { getApiBaseUrlLabel, toApiErrorMessage } from './apiClient'

export default function App() {
  const [screen,           setScreen]          = useState('explorer')   // 'explorer' | 'analysis'
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [loading,          setLoading]          = useState(false)
  const [result,           setResult]           = useState(null)
  const [observation,      setObservation]      = useState(null)
  const [error,            setError]            = useState(null)
  const [animKey,          setAnimKey]          = useState(0)

  useEffect(() => {
    getHealth().catch(console.error)
  }, [])

  const doRun = async (scenario) => {
    setLoading(true)
    setResult(null)
    setObservation(null)
    setError(null)
    try {
      const agentResult = await runAgent(scenario.task_id, scenario.seed)
      const obs         = await getState()
      setResult(agentResult)
      setObservation(obs)
      setAnimKey(k => k + 1)
    } catch (err) {
      setError(toApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleSelectScenario = (scenario) => {
    setSelectedScenario(scenario)
    setScreen('analysis')
    setResult(null)
    setObservation(null)
    setError(null)
    doRun(scenario)
  }

  const handleReRun = () => {
    if (selectedScenario) doRun(selectedScenario)
  }

  const handleBack = () => {
    setScreen('explorer')
    setResult(null)
    setObservation(null)
    setError(null)
  }

  return (
    <div className="h-full flex flex-col bg-bg">

      {/* ── HEADER ──────────────────────────────────── */}
      <header className="flex-shrink-0 border-b border-[#1f1f35] bg-[#060610] px-6 py-3 flex items-center justify-between">
        <button
          onClick={handleBack}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity"
        >
          <div className="relative">
            <div className="w-2 h-2 rounded-full bg-amber" />
            <div className="absolute inset-0 w-2 h-2 rounded-full bg-amber animate-ping opacity-40" />
          </div>
          <span className="font-display text-sm font-semibold tracking-[0.15em] uppercase text-amber">
            OpenENV
          </span>
          <span className="text-[#2a2a45]">│</span>
          <span className="text-[#3a3f5a] text-[11px] tracking-wide">
            Content Moderation Console
          </span>
        </button>

        <div className="flex items-center gap-4 text-[10px] text-[#3a3f5a]">
          {screen === 'analysis' && result && (
            <span className="text-[#5a5f7a]">
              last run ·{' '}
              <span className="text-amber">{result.task_id?.replace(/_/g, ' ')}</span>
            </span>
          )}
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4ade80] inline-block" />
            <span>API · {getApiBaseUrlLabel()}</span>
          </div>
        </div>
      </header>

      {/* ── SCREENS ─────────────────────────────────── */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {screen === 'explorer' ? (
          <ScenarioExplorer onSelect={handleSelectScenario} />
        ) : (
          <AnalysisView
            scenario={selectedScenario}
            observation={observation}
            result={result}
            loading={loading}
            error={error}
            animKey={animKey}
            onRun={handleReRun}
            onBack={handleBack}
          />
        )}
      </div>

    </div>
  )
}
