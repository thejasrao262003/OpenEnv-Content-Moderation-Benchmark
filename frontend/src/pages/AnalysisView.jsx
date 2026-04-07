import PostPanel from '../components/PostPanel'
import AgentPanel from '../components/AgentPanel'
import { DIFFICULTY_META } from '../data/scenarios'

const GEO_FLAG = { US: '🇺🇸', EU: '🇪🇺', IN: '🇮🇳', UK: '🇬🇧' }

export default function AnalysisView({
  scenario,
  observation,
  result,
  loading,
  error,
  animKey,
  onRun,
  onBack,
}) {
  const difficulty = scenario?.id?.split('-')[0] || 'easy'
  const meta       = DIFFICULTY_META[difficulty] || {}

  return (
    <div className="flex flex-col h-full slide-in">

      {/* Sub-header: back + scenario context */}
      <div className="flex-shrink-0 px-5 py-2.5 border-b border-[#1f1f35] bg-[#060610] flex items-center gap-4">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-[10px] text-[#3a3f5a] hover:text-[#dde1f0] transition-colors tracking-widest uppercase"
        >
          ← Back
        </button>
        <div className="w-px h-4 bg-[#1f1f35]" />
        <div className="flex items-center gap-2">
          <span
            className="text-[9px] font-semibold px-2 py-0.5 rounded tracking-widest uppercase"
            style={{ color: meta.color, background: `${meta.color}15`, border: `1px solid ${meta.color}35` }}
          >
            {meta.label}
          </span>
          {scenario?.preview?.geo && (
            <span className="text-[11px] text-[#3a3f5a]">
              {GEO_FLAG[scenario.preview.geo]} {scenario.preview.geo}
            </span>
          )}
          <span className="text-[10px] text-[#4a4f6a] truncate max-w-xs">
            {scenario?.why}
          </span>
        </div>
      </div>

      {/* Two-panel layout */}
      <div className="flex-1 grid grid-cols-[45%_55%] min-h-0">
        <PostPanel
          selectedTask={scenario?.task_id}
          onTaskChange={() => {}}
          observation={observation}
          loading={loading}
          onRun={onRun}
          hideSelector
        />
        <AgentPanel
          result={result}
          observation={observation}
          loading={loading}
          error={error}
          animKey={animKey}
        />
      </div>

    </div>
  )
}
