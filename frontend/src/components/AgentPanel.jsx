import StepTimeline from './StepTimeline'
import ScoreCard from './ScoreCard'
import { generateReasoning, getRegionalComparison } from '../utils'

const DECISION_STYLE = {
  remove:   { color: '#f87171', glow: 'glow-red',    border: 'rgba(248,113,113,0.25)', bg: 'rgba(248,113,113,0.05)' },
  allow:    { color: '#4ade80', glow: 'glow-green',  border: 'rgba(74,222,128,0.25)',  bg: 'rgba(74,222,128,0.05)'  },
  flag:     { color: '#fb923c', glow: 'glow-orange', border: 'rgba(251,146,60,0.25)',  bg: 'rgba(251,146,60,0.05)'  },
  escalate: { color: '#c084fc', glow: 'glow-purple', border: 'rgba(192,132,252,0.25)', bg: 'rgba(192,132,252,0.05)' },
}

const SEVERITY_COLOR = {
  critical: '#f87171', high: '#fb923c', medium: '#fbbf24', low: '#60a5fa',
}
const VIOLATION_COLOR = {
  harassment: '#f87171', misinformation: '#fb923c', restricted: '#fbbf24', safe: '#4ade80',
}

const REGION_LABELS = { US: '🇺🇸 US', EU: '🇪🇺 EU', IN: '🇮🇳 IN', UK: '🇬🇧 UK' }
const REGION_ORDER  = ['US', 'EU', 'IN', 'UK']

function SectionLabel({ children }) {
  return (
    <div className="flex items-center gap-3 mb-3">
      <span className="text-[9px] text-[#3a3f5a] tracking-[0.2em] uppercase">{children}</span>
      <div className="flex-1 h-px bg-[#1f1f35]" />
    </div>
  )
}

function Chip({ label, color }) {
  return (
    <span
      className="text-[10px] px-2 py-0.5 rounded tracking-widest uppercase font-medium"
      style={{ color, background: `${color}18`, border: `1px solid ${color}40` }}
    >
      {label}
    </span>
  )
}

function ActionPill({ action }) {
  const ds = DECISION_STYLE[action] || { color: '#5a5f7a', border: 'rgba(90,95,122,0.3)', bg: 'transparent' }
  return (
    <span
      className="text-[11px] font-semibold px-2 py-0.5 rounded tracking-wide uppercase"
      style={{ color: ds.color, background: ds.bg, border: `1px solid ${ds.border}` }}
    >
      {action}
    </span>
  )
}

function LoadingSkeleton({ llmProvider }) {
  const modelName = llmProvider === 'gemini' ? 'Gemini 2.5 Flash' : (llmProvider === 'openai' ? 'OpenAI GPT-4o mini' : 'Agent')
  return (
    <div className="p-5 space-y-4">
      <div className="border border-[#1f1f35] rounded p-5 space-y-3">
        <div className="h-3 w-24 bg-[#0f0f1a] rounded animate-pulse border border-[#1f1f35]" />
        <div className="h-12 w-40 bg-[#0f0f1a] rounded animate-pulse border border-[#1f1f35]" />
        <div className="h-3 w-64 bg-[#0f0f1a] rounded animate-pulse border border-[#1f1f35]" />
        <div className="h-3 w-48 bg-[#0f0f1a] rounded animate-pulse border border-[#1f1f35]" />
      </div>
      <div className="space-y-2 pt-2">
        {[1, 0.85, 0.7, 0.55, 0.4].map((op, i) => (
          <div
            key={i}
            className="h-14 bg-[#0f0f1a] rounded animate-pulse border border-[#1f1f35]"
            style={{ animationDelay: `${i * 0.08}s`, opacity: op }}
          />
        ))}
      </div>
      <div className="text-center text-[11px] text-amber animate-scanPulse pt-1">
        ◎ &nbsp; {modelName} reasoning...
      </div>
    </div>
  )
}

export default function AgentPanel({ result, observation, loading, error, animKey, llmProvider }) {
  const breakdown = result?.score?.breakdown

  if (loading) return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="px-5 py-3 border-b border-[#1f1f35] bg-[#0a0a14]">
        <div className="text-[9px] text-[#3a3f5a] tracking-[0.2em] uppercase mb-0.5">Output</div>
        <div className="font-display text-base font-semibold text-amber animate-scanPulse">Agent Analyzing</div>
      </div>
      <LoadingSkeleton llmProvider={llmProvider} />
    </div>
  )

  if (error) return (
    <div className="flex flex-col h-full overflow-y-auto">
      <div className="px-5 py-3 border-b border-[#1f1f35] bg-[#0a0a14]">
        <div className="text-[9px] text-[#3a3f5a] tracking-[0.2em] uppercase mb-0.5">Output</div>
        <div className="font-display text-base font-semibold text-[#f87171]">Error</div>
      </div>
      <div className="p-5">
        <div className="border border-[#f87171]/30 rounded p-4 text-[11px] text-[#f87171]">{error}</div>
      </div>
    </div>
  )

  if (!result) return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-3 border-b border-[#1f1f35] bg-[#0a0a14]">
        <div className="text-[9px] text-[#3a3f5a] tracking-[0.2em] uppercase mb-0.5">Output</div>
        <div className="font-display text-base font-semibold text-[#dde1f0]">Agent Analysis</div>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center gap-3 p-8 text-center">
        <div className="text-3xl text-[#1f1f35]">◌</div>
        <div className="text-[11px] text-[#3a3f5a] leading-relaxed max-w-44">
          Select a scenario and run the AI agent to see its reasoning and decision
        </div>
      </div>
    </div>
  )

  const action    = breakdown?.agent_action
  const expected  = breakdown?.expected_action
  const isCorrect = action === expected
  const ds        = DECISION_STYLE[action] || { color: '#5a5f7a', glow: '', border: 'rgba(90,95,122,0.2)', bg: 'transparent' }
  const sevColor  = SEVERITY_COLOR[breakdown?.final_severity] || '#5a5f7a'
  const vioColor  = VIOLATION_COLOR[breakdown?.violation_type] || '#5a5f7a'

  const reasoning = generateReasoning(breakdown, result.trajectory)
  const regional  = getRegionalComparison(breakdown?.violation_type, breakdown?.final_severity)
  const currentGeo = observation?.geo || null

  return (
    <div key={animKey} className="flex flex-col h-full overflow-y-auto">

      {/* Header */}
      <div className="px-5 py-3 border-b border-[#1f1f35] bg-[#0a0a14] flex items-center justify-between">
        <div>
          <div className="text-[9px] text-[#3a3f5a] tracking-[0.2em] uppercase mb-0.5">Output</div>
          <div className="font-display text-base font-semibold text-[#dde1f0]">Agent Analysis</div>
        </div>
        <div className="text-[10px] text-[#3a3f5a]">
          {result.trajectory?.length} step{result.trajectory?.length !== 1 ? 's' : ''}
        </div>
      </div>

      <div className="flex-1 p-5 space-y-5">

        {/* ── 1. DECISION CARD ──────────────────────────── */}
        <div
          className="rounded border p-4 fade-up"
          style={{ borderColor: ds.border, background: ds.bg }}
        >
          {/* Giant decision word */}
          <div className="text-[9px] text-[#3a3f5a] tracking-[0.2em] uppercase mb-1.5">Final Decision</div>
          <div
            className={`font-display font-bold leading-none mb-3 ${ds.glow}`}
            style={{ fontSize: '48px', color: ds.color, letterSpacing: '-0.02em' }}
          >
            {action?.toUpperCase() ?? 'NO DECISION'}
          </div>

          {/* Expected vs actual */}
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            <div className="flex items-center gap-1.5 text-[11px]">
              <span className="text-[#3a3f5a]">Agent:</span>
              <ActionPill action={action} />
              <span style={{ color: isCorrect ? '#4ade80' : '#f87171', fontSize: '14px' }}>
                {isCorrect ? '✓' : '✗'}
              </span>
            </div>
            {!isCorrect && (
              <div className="flex items-center gap-1.5 text-[11px]">
                <span className="text-[#3a3f5a]">Expected:</span>
                <ActionPill action={expected} />
              </div>
            )}
          </div>

          {/* Chips */}
          <div className="flex items-center gap-2 flex-wrap mb-3">
            {breakdown?.violation_type && <Chip label={breakdown.violation_type} color={vioColor} />}
            {breakdown?.final_severity  && <Chip label={breakdown.final_severity}  color={sevColor} />}
          </div>

          {/* Reasoning explanation */}
          <div className="border-t border-[#1f1f35] pt-3 mt-1">
            <div className="text-[9px] text-[#3a3f5a] tracking-[0.15em] uppercase mb-1.5">Reasoning</div>
            <p className="text-[11px] text-[#5a5f7a] leading-relaxed italic">
              &ldquo;{reasoning}&rdquo;
            </p>
          </div>
        </div>

        {/* ── 2. REGION COMPARISON ─────────────────────── */}
        <div className="fade-up" style={{ animationDelay: '0.08s' }}>
          <SectionLabel>Policy Comparison by Region</SectionLabel>
          <div className="grid grid-cols-4 gap-2">
            {REGION_ORDER.map(geo => {
              const decision = regional[geo] || 'allow'
              const dStyle   = DECISION_STYLE[decision] || { color: '#5a5f7a', border: 'rgba(90,95,122,0.2)', bg: 'transparent' }
              const isCurrent = geo === currentGeo
              return (
                <div
                  key={geo}
                  className="rounded border p-2.5 text-center transition-all"
                  style={{
                    borderColor: isCurrent ? dStyle.color : 'rgba(30,30,50,1)',
                    background:  isCurrent ? dStyle.bg    : '#0a0a12',
                    boxShadow:   isCurrent ? `0 0 12px ${dStyle.color}20` : 'none',
                  }}
                >
                  <div className="text-[11px] mb-1">{REGION_LABELS[geo]}</div>
                  <div
                    className="text-[10px] font-semibold uppercase tracking-wide"
                    style={{ color: dStyle.color }}
                  >
                    {decision}
                  </div>
                  {isCurrent && (
                    <div className="text-[8px] text-[#3a3f5a] mt-1 tracking-wide">current</div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* ── 3. TRAJECTORY ────────────────────────────── */}
        <div className="fade-up" style={{ animationDelay: '0.14s' }}>
          <SectionLabel>Agent Trajectory</SectionLabel>
          <StepTimeline trajectory={result.trajectory} animKey={animKey} />
        </div>

        {/* ── 4. SCORE BREAKDOWN ───────────────────────── */}
        <div
          className="fade-up border border-[#1f1f35] rounded p-4"
          style={{ animationDelay: '0.2s' }}
        >
          <SectionLabel>Performance Breakdown</SectionLabel>
          <ScoreCard score={result.score} animKey={animKey} />
        </div>

      </div>
    </div>
  )
}
