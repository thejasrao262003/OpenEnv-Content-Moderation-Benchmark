const METRICS = [
  {
    key: 'final_action_score',
    label: 'Final Action Accuracy',
    weight: '50%',
    desc: 'Did the agent take the correct terminal action (allow/flag/remove/escalate)?',
  },
  {
    key: 'classification_score',
    label: 'Classification Accuracy',
    weight: '20%',
    desc: 'Did the agent correctly identify the violation type?',
  },
  {
    key: 'investigation_score',
    label: 'Investigation Quality',
    weight: '15%',
    desc: 'Did the agent gather all recommended context before deciding?',
  },
  {
    key: 'efficiency_score',
    label: 'Efficiency',
    weight: '15%',
    desc: 'Did the agent reach a decision without unnecessary extra steps?',
  },
]

function barColor(v) {
  if (v >= 0.8) return '#4ade80'
  if (v >= 0.5) return '#f0a500'
  return '#f87171'
}

function Tooltip({ text }) {
  return (
    <span className="group relative cursor-default">
      <span className="text-[9px] text-[#3a3f5a] border border-[#2a2a45] rounded-full px-1 leading-none select-none">?</span>
      <span className="absolute left-0 bottom-full mb-1.5 w-48 bg-[#0f0f1a] border border-[#2a2a45] rounded p-2 text-[10px] text-[#5a5f7a] leading-relaxed z-10 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-150 shadow-xl">
        {text}
      </span>
    </span>
  )
}

function ScoreBar({ value, animKey }) {
  const color = barColor(value)
  return (
    <div className="relative h-1 bg-[#1f1f35] rounded-full overflow-hidden">
      <div
        key={animKey}
        className="absolute inset-y-0 left-0 rounded-full score-bar"
        style={{
          width: `${Math.round(value * 100)}%`,
          background: color,
          boxShadow: `0 0 6px ${color}80`,
        }}
      />
    </div>
  )
}

export default function ScoreCard({ score, animKey }) {
  if (!score) return null

  const total = score.total
  const totalColor = barColor(total)
  const isCorrect = score.final_action_score === 1.0

  return (
    <div className="space-y-4">
      {/* Total */}
      <div className="flex items-end justify-between pb-3 border-b border-[#1f1f35]">
        <div>
          <div className="text-[9px] text-[#3a3f5a] tracking-[0.18em] uppercase mb-1">
            Total Score
          </div>
          <div
            className="font-display font-bold tabular-nums leading-none"
            style={{ fontSize: '42px', color: totalColor, textShadow: `0 0 18px ${totalColor}55` }}
          >
            {Math.round(total * 100)}
            <span className="text-lg font-medium ml-0.5" style={{ color: `${totalColor}88` }}>
              %
            </span>
          </div>
        </div>
        <div className="text-right space-y-1">
          {/* Correct / wrong indicator */}
          <div
            className="text-xs font-semibold px-2 py-0.5 rounded"
            style={
              isCorrect
                ? { color: '#4ade80', background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.3)' }
                : { color: '#f87171', background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.3)' }
            }
          >
            {isCorrect ? '✓ Correct Decision' : '✗ Wrong Decision'}
          </div>
          {score.breakdown?.false_negative_penalty > 0 && (
            <div className="text-[10px] text-[#f87171]">
              ⚠ false negative −{score.breakdown.false_negative_penalty.toFixed(2)}
            </div>
          )}
        </div>
      </div>

      {/* Per-metric bars */}
      <div className="space-y-3.5">
        {METRICS.map(({ key, label, weight, desc }) => {
          const v = score[key] ?? 0
          const color = barColor(v)
          return (
            <div key={key}>
              <div className="flex justify-between items-center mb-1.5">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] text-[#5a5f7a]">{label}</span>
                  <Tooltip text={desc} />
                  <span className="text-[9px] text-[#2a2a45] tracking-widest ml-0.5">{weight}</span>
                </div>
                <span
                  className="text-xs tabular-nums font-semibold"
                  style={{ color }}
                >
                  {Math.round(v * 100)}%
                </span>
              </div>
              <ScoreBar value={v} animKey={`${animKey}-${key}`} />
            </div>
          )
        })}
      </div>
    </div>
  )
}
