import { SCENARIOS, DIFFICULTY_META } from '../data/scenarios'
import PostCard from '../components/PostCard'

function DifficultySection({ difficulty, scenarios, onSelect }) {
  const meta = DIFFICULTY_META[difficulty]
  return (
    <div className="mb-8">
      {/* Section header */}
      <div className="flex items-center gap-3 mb-4">
        <div
          className="text-[10px] font-semibold px-2.5 py-1 rounded tracking-widest uppercase"
          style={{ color: meta.color, background: `${meta.color}15`, border: `1px solid ${meta.color}35` }}
        >
          {meta.label}
        </div>
        <div className="flex-1 h-px bg-[#1f1f35]" />
        <span className="text-[10px] text-[#3a3f5a]">{scenarios.length} scenarios</span>
      </div>

      {/* Description */}
      <p className="text-[11px] text-[#3a3f5a] mb-4 leading-relaxed">{meta.desc}</p>

      {/* Card grid */}
      <div className="grid grid-cols-3 gap-3">
        {scenarios.map(scenario => (
          <PostCard
            key={scenario.id}
            scenario={scenario}
            difficulty={difficulty}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  )
}

export default function ScenarioExplorer({ onSelect }) {
  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Page header */}
      <div className="flex-shrink-0 px-8 py-6 border-b border-[#1f1f35] bg-[#060610]">
        <div className="text-[9px] text-[#3a3f5a] tracking-[0.2em] uppercase mb-1">
          Step 1 of 2
        </div>
        <h1 className="font-display text-xl font-semibold text-[#dde1f0] mb-1">
          Select a Scenario
        </h1>
        <p className="text-[12px] text-[#4a4f6a] leading-relaxed">
          Choose a content moderation challenge. The AI agent will analyze it in real time.
        </p>
      </div>

      {/* Scenario grid */}
      <div className="flex-1 px-8 py-6">
        {['easy', 'medium', 'hard'].map(diff => (
          <DifficultySection
            key={diff}
            difficulty={diff}
            scenarios={SCENARIOS[diff]}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  )
}
