import { useState, useEffect } from 'react'

const ACTION_META = {
  fetch_user_history:   { tag: 'INV', color: '#60a5fa', border: 'rgba(96,165,250,0.3)',   bg: 'rgba(59,130,246,0.06)'  },
  fetch_thread_context: { tag: 'INV', color: '#60a5fa', border: 'rgba(96,165,250,0.3)',   bg: 'rgba(59,130,246,0.06)'  },
  check_policy_clause:  { tag: 'INV', color: '#60a5fa', border: 'rgba(96,165,250,0.3)',   bg: 'rgba(59,130,246,0.06)'  },
  mark_violation_type:  { tag: 'CLS', color: '#fbbf24', border: 'rgba(251,191,36,0.3)',   bg: 'rgba(251,191,36,0.06)'  },
  allow:    { tag: 'END', color: '#4ade80', border: 'rgba(74,222,128,0.4)',  bg: 'rgba(74,222,128,0.07)'  },
  flag:     { tag: 'END', color: '#fb923c', border: 'rgba(251,146,60,0.4)',  bg: 'rgba(251,146,60,0.07)'  },
  remove:   { tag: 'END', color: '#f87171', border: 'rgba(248,113,113,0.4)', bg: 'rgba(248,113,113,0.07)' },
  escalate: { tag: 'END', color: '#c084fc', border: 'rgba(192,132,252,0.4)', bg: 'rgba(192,132,252,0.07)' },
}

const INV_LABELS = {
  fetch_user_history:   'Fetched user violation history',
  fetch_thread_context: 'Retrieved conversation thread context',
  check_policy_clause:  'Loaded applicable policy clause',
  mark_violation_type:  'Classified violation type',
  allow:    'Decision: Allow content',
  flag:     'Decision: Flag for review',
  remove:   'Decision: Remove content',
  escalate: 'Decision: Escalate to senior moderator',
}

function RewardSign({ value }) {
  const isPos = value >= 0
  return (
    <span className="tabular-nums" style={{ color: isPos ? '#4ade80' : '#f87171' }}>
      {isPos ? '+' : ''}{value.toFixed(2)}
    </span>
  )
}

export default function StepTimeline({ trajectory, animKey }) {
  const [visibleCount, setVisibleCount] = useState(0)

  // Reveal steps one by one whenever trajectory/animKey changes
  useEffect(() => {
    setVisibleCount(0)
    if (!trajectory?.length) return
    let count = 0
    const id = setInterval(() => {
      count += 1
      setVisibleCount(count)
      if (count >= trajectory.length) clearInterval(id)
    }, 380)
    return () => clearInterval(id)
  }, [animKey, trajectory])

  if (!trajectory?.length) return null

  const visible = trajectory.slice(0, visibleCount)

  return (
    <div className="space-y-2">
      {visible.map((item, i) => {
        const at   = item.action.action_type
        const meta = ACTION_META[at] || { tag: '?', color: '#5a5f7a', border: 'rgba(90,95,122,0.3)', bg: 'transparent' }
        const isTerminal = meta.tag === 'END'
        const params = item.action.parameters

        return (
          <div
            key={`${animKey}-${i}`}
            className="rounded overflow-hidden"
            style={{
              border: `1px solid ${meta.border}`,
              background: meta.bg,
              animation: 'stepReveal 0.32s ease forwards',
            }}
          >
            <div className="flex items-start gap-3 px-3 py-2.5">
              {/* Step index + type tag */}
              <div className="flex-shrink-0 flex items-center gap-2 pt-px">
                <span className="text-[#3a3f5a] text-[10px] tabular-nums w-4">
                  {String(item.step).padStart(2, '0')}
                </span>
                <span
                  className="text-[9px] font-semibold px-1.5 py-px rounded-sm tracking-widest"
                  style={{
                    color: meta.color,
                    background: `${meta.color}18`,
                    border: `1px solid ${meta.border}`,
                  }}
                >
                  {meta.tag}
                </span>
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline justify-between gap-2">
                  <span
                    className="font-medium tracking-tight"
                    style={{ color: meta.color, fontSize: '12px' }}
                  >
                    {at}
                  </span>
                  <span className="text-xs flex-shrink-0">
                    <RewardSign value={item.reward} />
                  </span>
                </div>

                {/* Human-readable label */}
                <div className="mt-0.5 text-[10px] text-[#5a5f7a]">
                  {INV_LABELS[at] || at}
                </div>

                {/* Parameters for mark_violation_type */}
                {at === 'mark_violation_type' && params?.violation_type && (
                  <div className="mt-1 text-[10px] text-[#3a3f5a]">
                    violation_type = <span style={{ color: '#fbbf24' }}>&quot;{params.violation_type}&quot;</span>
                  </div>
                )}

                {/* Reward reason (dimmed, compact) */}
                <div className="mt-0.5 text-[10px] text-[#2a2a45] truncate">
                  {item.reward_reason}
                </div>
              </div>
            </div>

            {/* Terminal bottom accent */}
            {isTerminal && (
              <div
                className="h-px w-full"
                style={{ background: `linear-gradient(90deg, ${meta.color}70, transparent)` }}
              />
            )}
          </div>
        )
      })}

      {/* Pending steps placeholder — shows how many are still to animate */}
      {visibleCount < trajectory.length && (
        <div className="flex items-center gap-2 px-3 py-1.5">
          <span className="animate-scanPulse text-[#3a3f5a] text-xs">◎</span>
          <span className="text-[10px] text-[#3a3f5a]">
            {trajectory.length - visibleCount} more step{trajectory.length - visibleCount !== 1 ? 's' : ''}...
          </span>
        </div>
      )}
    </div>
  )
}
