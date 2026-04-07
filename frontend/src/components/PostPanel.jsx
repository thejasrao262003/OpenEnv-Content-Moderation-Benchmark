const TASKS = [
  { id: 'easy_harassment',    label: 'Easy — Clear Harassment',        diff: 'EASY',   color: '#4ade80' },
  { id: 'medium_ambiguous',   label: 'Medium — Ambiguous Review',      diff: 'MED',    color: '#f0a500' },
  { id: 'hard_misinformation',label: 'Hard — Health Misinformation',   diff: 'HARD',   color: '#f87171' },
]

const GEO_LABELS = { US: '🇺🇸 US', EU: '🇪🇺 EU', IN: '🇮🇳 IN' }

function MetaBadge({ label, value, accent }) {
  return (
    <div className="flex flex-col gap-1 p-3 bg-[#0f0f1a] border border-[#1f1f35] rounded">
      <span className="text-[9px] text-[#3a3f5a] tracking-[0.15em] uppercase">{label}</span>
      <span className="text-sm font-medium" style={{ color: accent || '#dde1f0' }}>{value}</span>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="border border-[#1f1f35] rounded overflow-hidden">
      <div className="px-3 py-1.5 bg-[#0f0f1a] border-b border-[#1f1f35]">
        <span className="text-[9px] text-[#3a3f5a] tracking-[0.2em] uppercase">{title}</span>
      </div>
      <div className="p-3">{children}</div>
    </div>
  )
}

export default function PostPanel({ selectedTask, onTaskChange, observation, loading, onRun, hideSelector }) {
  const task = TASKS.find(t => t.id === selectedTask) || TASKS[0]

  return (
    <div className="flex flex-col h-full border-r border-[#1f1f35] overflow-y-auto">

      {/* Panel header */}
      <div className="px-5 py-3 border-b border-[#1f1f35] bg-[#0a0a14]">
        <div className="text-[9px] text-[#3a3f5a] tracking-[0.2em] uppercase mb-0.5">Input</div>
        <div className="font-display text-base font-semibold text-[#dde1f0]">Content Review</div>
      </div>

      <div className="flex-1 p-5 space-y-4">

        {/* Task selector — hidden when coming from scenario explorer */}
        {!hideSelector && (
          <div className="space-y-2">
            <label className="text-[9px] text-[#3a3f5a] tracking-[0.18em] uppercase block">
              Task Scenario
            </label>
            <div className="relative">
              <select
                value={selectedTask}
                onChange={e => onTaskChange(e.target.value)}
                disabled={loading}
                className="w-full appearance-none bg-[#0f0f1a] border border-[#1f1f35] text-[#dde1f0] text-xs px-3 py-2.5 rounded focus:outline-none focus:border-[#f0a500] cursor-pointer disabled:opacity-50 transition-colors pr-8"
              >
                {TASKS.map(t => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-[#3a3f5a]">
                ▾
              </div>
            </div>
            {/* Difficulty badge */}
            <div className="flex items-center gap-2">
              <div
                className="text-[9px] px-2 py-0.5 rounded tracking-widest font-medium"
                style={{ color: task.color, background: `${task.color}18`, border: `1px solid ${task.color}40` }}
              >
                {task.diff}
              </div>
              <span className="text-[10px] text-[#3a3f5a]">difficulty</span>
            </div>
          </div>
        )}

        {/* Run button */}
        <button
          onClick={onRun}
          disabled={loading}
          className="w-full py-3 px-4 rounded border transition-all duration-200 font-medium text-xs tracking-widest uppercase disabled:opacity-60 disabled:cursor-not-allowed"
          style={
            loading
              ? { color: '#f0a500', borderColor: 'rgba(240,165,0,0.3)', background: 'rgba(240,165,0,0.04)' }
              : {
                  color: '#080810',
                  background: '#f0a500',
                  borderColor: '#f0a500',
                  boxShadow: '0 0 20px rgba(240,165,0,0.25)',
                }
          }
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-scanPulse">◎</span>
              <span>ANALYZING...</span>
            </span>
          ) : (
            '▶  RUN AI AGENT'
          )}
        </button>

        {/* Divider */}
        <div className="border-t border-[#1f1f35]" />

        {/* Post content */}
        {!observation && !loading && (
          <div
            className="border border-dashed border-[#1f1f35] rounded p-5 text-center"
          >
            <div className="text-[#3a3f5a] text-xs mb-1">◌</div>
            <div className="text-[11px] text-[#3a3f5a]">
              Post content will appear after the agent runs
            </div>
          </div>
        )}

        {loading && (
          <div className="space-y-2">
            {[0.9, 0.7, 0.85, 0.6].map((w, i) => (
              <div
                key={i}
                className="h-3 bg-[#0f0f1a] rounded animate-pulse border border-[#1f1f35]"
                style={{ width: `${w * 100}%`, animationDelay: `${i * 0.1}s` }}
              />
            ))}
          </div>
        )}

        {observation && !loading && (
          <>
            {/* Post content card */}
            <Section title="Post Content">
              <p className="text-sm leading-relaxed text-[#dde1f0] italic">
                &ldquo;{observation.content}&rdquo;
              </p>
            </Section>

            {/* Metadata grid */}
            <div className="grid grid-cols-3 gap-2">
              <MetaBadge label="Geo"     value={GEO_LABELS[observation.geo] || observation.geo} accent="#60a5fa" />
              <MetaBadge label="Reports" value={observation.reports} accent="#f87171" />
              <MetaBadge
                label="Engagement"
                value={`${(observation.engagement?.likes || 0) + (observation.engagement?.shares || 0) + (observation.engagement?.comments || 0)}`}
                accent="#f0a500"
              />
            </div>

            {/* Engagement breakdown */}
            <div className="grid grid-cols-3 gap-2">
              <MetaBadge label="Likes"    value={observation.engagement?.likes    ?? '–'} />
              <MetaBadge label="Shares"   value={observation.engagement?.shares   ?? '–'} />
              <MetaBadge label="Comments" value={observation.engagement?.comments ?? '–'} />
            </div>

            {/* User history */}
            {observation.user_history && (
              <Section title="User History">
                <ul className="space-y-1.5">
                  {observation.user_history.map((h, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px]">
                      <span className="text-[#f87171] flex-shrink-0 mt-px">●</span>
                      <span className="text-[#5a5f7a] leading-relaxed">{h}</span>
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {/* Thread context */}
            {observation.thread_context && (
              <Section title="Thread Context">
                <ul className="space-y-1.5">
                  {observation.thread_context.map((t, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px]">
                      <span className="text-[#60a5fa] flex-shrink-0 mt-px">›</span>
                      <span className="text-[#5a5f7a] leading-relaxed">{t}</span>
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {/* Policy clause */}
            {observation.policy_clause && (
              <Section title="Policy Clause">
                <p className="text-[11px] text-[#5a5f7a] leading-relaxed">
                  {observation.policy_clause}
                </p>
              </Section>
            )}
          </>
        )}
      </div>
    </div>
  )
}
