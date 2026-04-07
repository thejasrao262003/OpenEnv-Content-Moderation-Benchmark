import { DIFFICULTY_META } from '../data/scenarios'

const GEO_FLAG = { US: '🇺🇸', EU: '🇪🇺', IN: '🇮🇳', UK: '🇬🇧' }

export default function PostCard({ scenario, difficulty, onSelect }) {
  const meta    = DIFFICULTY_META[difficulty]
  const preview = scenario.preview

  return (
    <button
      onClick={() => onSelect(scenario)}
      className="w-full text-left rounded border border-[#1f1f35] bg-[#0a0a14] p-4 transition-all duration-200 hover:border-[#2a2a45] hover:bg-[#0d0d1a] group relative overflow-hidden"
      style={{ '--accent': meta.color }}
    >
      {/* Hover accent line */}
      <div
        className="absolute top-0 left-0 right-0 h-px opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        style={{ background: `linear-gradient(90deg, transparent, ${meta.color}60, transparent)` }}
      />

      {/* Difficulty badge + geo */}
      <div className="flex items-center justify-between mb-3">
        <span
          className="text-[9px] font-semibold px-2 py-0.5 rounded tracking-widest uppercase"
          style={{ color: meta.color, background: `${meta.color}15`, border: `1px solid ${meta.color}35` }}
        >
          {meta.label}
        </span>
        <span className="text-xs text-[#3a3f5a]">
          {GEO_FLAG[preview.geo] || ''} {preview.geo}
        </span>
      </div>

      {/* Post content preview */}
      <p className="text-[12px] text-[#9aa0bc] leading-relaxed mb-3 line-clamp-3 italic">
        &ldquo;{preview.content}&rdquo;
      </p>

      {/* Engagement row */}
      <div className="flex items-center gap-3 mb-3 text-[10px] text-[#3a3f5a]">
        <span>
          <span className="text-[#f87171]">▲</span> {preview.reports} reports
        </span>
        <span className="text-[#2a2a45]">·</span>
        <span>{preview.likes} likes</span>
        <span className="text-[#2a2a45]">·</span>
        <span>{preview.shares} shares</span>
        <span className="text-[#2a2a45]">·</span>
        <span>{preview.comments} comments</span>
      </div>

      {/* Divider */}
      <div className="border-t border-[#1f1f35] mb-3" />

      {/* Why explanation */}
      <div className="flex items-start gap-2">
        <span className="text-[9px] text-[#3a3f5a] tracking-widest uppercase mt-px flex-shrink-0">Why</span>
        <p className="text-[10px] text-[#4a4f6a] leading-relaxed">
          {scenario.why}
        </p>
      </div>

      {/* Run arrow — appears on hover */}
      <div
        className="absolute right-4 bottom-4 text-[10px] font-semibold tracking-widest uppercase opacity-0 group-hover:opacity-100 transition-all duration-200 translate-x-1 group-hover:translate-x-0"
        style={{ color: meta.color }}
      >
        Run →
      </div>
    </button>
  )
}
