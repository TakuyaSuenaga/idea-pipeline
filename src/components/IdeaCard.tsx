import { useState } from 'react'
import type { Idea } from '../types'

const CATEGORY_STYLES: Record<string, string> = {
  saas: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  seo: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
}

const DIFFICULTY_STYLES: Record<string, string> = {
  low: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  high: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
}

const DIFFICULTY_LABELS: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

interface Props {
  idea: Idea
}

export default function IdeaCard({ idea }: Props) {
  const [expanded, setExpanded] = useState(false)

  return (
    <article className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 flex flex-col gap-3 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-2">
        <h3 className="font-semibold text-sm leading-snug flex-1 text-gray-900 dark:text-white">
          {idea.title}
        </h3>
        <div className="flex gap-1 shrink-0 flex-wrap justify-end">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CATEGORY_STYLES[idea.category] ?? ''}`}>
            {idea.category.toUpperCase()}
          </span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${DIFFICULTY_STYLES[idea.difficulty] ?? ''}`}>
            難易度{DIFFICULTY_LABELS[idea.difficulty] ?? idea.difficulty}
          </span>
        </div>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
        {idea.description}
      </p>

      {expanded && (
        <dl className="text-sm space-y-2 border-t border-gray-100 dark:border-gray-700 pt-3">
          {idea.target_market && (
            <>
              <dt className="font-medium text-gray-700 dark:text-gray-300">ターゲット市場</dt>
              <dd className="text-gray-600 dark:text-gray-400">{idea.target_market}</dd>
            </>
          )}
          {idea.why_now && (
            <>
              <dt className="font-medium text-gray-700 dark:text-gray-300 mt-2">Why Now</dt>
              <dd className="text-gray-600 dark:text-gray-400">{idea.why_now}</dd>
            </>
          )}
          {idea.revenue_model && (
            <>
              <dt className="font-medium text-gray-700 dark:text-gray-300 mt-2">収益モデル</dt>
              <dd className="text-gray-600 dark:text-gray-400">{idea.revenue_model}</dd>
            </>
          )}
        </dl>
      )}

      <div className="flex items-center justify-between mt-auto pt-1">
        <time className="text-xs text-gray-400 dark:text-gray-500">
          {new Date(idea.generated_at).toLocaleDateString('ja-JP')}
        </time>
        <button
          onClick={() => setExpanded((e) => !e)}
          className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
        >
          {expanded ? '閉じる' : '詳細を見る'}
        </button>
      </div>
    </article>
  )
}
