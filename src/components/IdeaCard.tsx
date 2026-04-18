import { useState } from 'react'
import type { Idea } from '../types'

const DIFF_LABELS: Record<string, string> = { low: '低', medium: '中', high: '高' }

function scoreColor(v: number): string {
  if (v >= 8) return 'var(--diff-low)'
  if (v >= 5) return 'var(--amber)'
  return 'var(--diff-high)'
}

interface Props {
  idea: Idea
  index: number
}

export default function IdeaCard({ idea, index }: Props) {
  const [expanded, setExpanded] = useState(false)

  const catFg = idea.category === 'saas' ? 'var(--saas-fg)' : 'var(--seo-fg)'
  const catBg = idea.category === 'saas' ? 'var(--saas-bg)' : 'var(--seo-bg)'
  const diffColor =
    idea.difficulty === 'low'
      ? 'var(--diff-low)'
      : idea.difficulty === 'medium'
        ? 'var(--diff-med)'
        : 'var(--diff-high)'

  return (
    <li style={{ borderBottom: '1px solid var(--border)' }}>
      <button
        className="w-full text-left flex items-start gap-4 py-5 group"
        onClick={() => setExpanded((e) => !e)}
      >
        {/* Number */}
        <span
          className="text-xs font-mono tabular-nums mt-0.5 shrink-0 w-6 text-right"
          style={{ color: 'var(--text-muted)' }}
        >
          {String(index).padStart(2, '0')}
        </span>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2 flex-wrap">
            <h3
              className="font-medium text-[15px] leading-snug flex-1 min-w-0 group-hover:opacity-80 transition-opacity"
              style={{ color: 'var(--text)' }}
            >
              {idea.title}
            </h3>
            <div className="flex items-center gap-2 shrink-0 mt-0.5">
              <span
                className="text-[10px] px-1.5 py-0.5 font-semibold rounded tracking-wide"
                style={{ color: catFg, background: catBg }}
              >
                {idea.category.toUpperCase()}
              </span>
              <span className="text-[11px] font-medium tabular-nums" style={{ color: diffColor }}>
                難易度{DIFF_LABELS[idea.difficulty] ?? idea.difficulty}
              </span>
              {idea.eval_total != null && (
                <span
                  className="text-[11px] font-mono tabular-nums"
                  style={{ color: scoreColor(idea.eval_total) }}
                >
                  ★{idea.eval_total.toFixed(1)}
                </span>
              )}
              <time className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                {new Date(idea.generated_at).toLocaleDateString('ja-JP', {
                  month: 'numeric',
                  day: 'numeric',
                })}
              </time>
              <span
                className="text-xs transition-transform duration-200"
                style={{
                  color: 'var(--text-muted)',
                  display: 'inline-block',
                  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                }}
              >
                ▾
              </span>
            </div>
          </div>
          <p className="text-sm mt-1.5 leading-relaxed" style={{ color: 'var(--text-sub)' }}>
            {idea.description}
          </p>
        </div>
      </button>

      {expanded && (
        <div className="pl-10 pb-5 space-y-4">
          {idea.why_now && (
            <div
              className="border-l-2 pl-4 py-2 rounded-r"
              style={{ borderColor: 'var(--amber)', background: 'var(--amber-bg)' }}
            >
              <p
                className="text-[10px] font-bold uppercase tracking-widest mb-1.5"
                style={{ color: 'var(--amber)' }}
              >
                Why Now
              </p>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text)' }}>
                {idea.why_now}
              </p>
            </div>
          )}

          {(idea.target_market || idea.revenue_model) && (
            <dl className="grid grid-cols-[5rem_1fr] gap-x-4 gap-y-2 text-sm">
              {idea.target_market && (
                <>
                  <dt
                    className="text-[10px] font-bold uppercase tracking-widest pt-0.5"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    市場
                  </dt>
                  <dd style={{ color: 'var(--text-sub)' }}>{idea.target_market}</dd>
                </>
              )}
              {idea.revenue_model && (
                <>
                  <dt
                    className="text-[10px] font-bold uppercase tracking-widest pt-0.5"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    収益
                  </dt>
                  <dd style={{ color: 'var(--text-sub)' }}>{idea.revenue_model}</dd>
                </>
              )}
            </dl>
          )}

          {(idea.eval_why_now != null || idea.eval_differentiation != null ||
            idea.eval_feasibility != null || idea.eval_market_size != null ||
            idea.eval_pain_point != null) && (
            <div>
              <p
                className="text-[10px] font-bold uppercase tracking-widest mb-2"
                style={{ color: 'var(--text-muted)' }}
              >
                評価
              </p>
              <div className="space-y-1.5">
                {([
                  { label: 'Why Now', value: idea.eval_why_now },
                  { label: '差別化', value: idea.eval_differentiation },
                  { label: '実現可能性', value: idea.eval_feasibility },
                  { label: '市場規模', value: idea.eval_market_size },
                  { label: 'Pain Point', value: idea.eval_pain_point },
                ] as { label: string; value: number | null }[]).map(({ label, value }) =>
                  value != null ? (
                    <div key={label} className="flex items-center gap-2">
                      <span
                        className="text-[10px] w-16 shrink-0"
                        style={{ color: 'var(--text-muted)' }}
                      >
                        {label}
                      </span>
                      <div
                        className="flex-1 h-1 rounded-full"
                        style={{ background: 'var(--border)' }}
                      >
                        <div
                          className="h-1 rounded-full transition-all"
                          style={{
                            width: `${value * 10}%`,
                            background: scoreColor(value),
                          }}
                        />
                      </div>
                      <span
                        className="text-[10px] tabular-nums w-4 text-right font-mono"
                        style={{ color: scoreColor(value) }}
                      >
                        {value}
                      </span>
                    </div>
                  ) : null
                )}
              </div>
              {idea.eval_comment && (
                <p className="text-xs mt-2 leading-relaxed" style={{ color: 'var(--text-sub)' }}>
                  {idea.eval_comment}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </li>
  )
}
