type CategoryFilter = 'all' | 'saas' | 'seo'
type DifficultyFilter = 'all' | 'low' | 'medium' | 'high'
export type SortOrder =
  | 'date_desc'
  | 'date_asc'
  | 'diff_high'
  | 'diff_low'
  | 'score_high'
  | 'score_low'

interface Props {
  category: CategoryFilter
  difficulty: DifficultyFilter
  sort: SortOrder
  onCategory: (c: CategoryFilter) => void
  onDifficulty: (d: DifficultyFilter) => void
  onSort: (s: SortOrder) => void
}

const CATEGORIES: { value: CategoryFilter; label: string }[] = [
  { value: 'all', label: 'すべて' },
  { value: 'saas', label: 'SaaS' },
  { value: 'seo', label: 'SEO' },
]

const DIFFICULTIES: { value: DifficultyFilter; label: string }[] = [
  { value: 'all', label: 'すべて' },
  { value: 'low', label: '低' },
  { value: 'medium', label: '中' },
  { value: 'high', label: '高' },
]

const SORT_OPTIONS: { value: SortOrder; label: string }[] = [
  { value: 'date_desc', label: '日付：新しい順' },
  { value: 'date_asc', label: '日付：古い順' },
  { value: 'diff_high', label: '難易度：高い順' },
  { value: 'diff_low', label: '難易度：低い順' },
  { value: 'score_high', label: 'スコア：高い順' },
  { value: 'score_low', label: 'スコア：低い順' },
]

function Pill({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className="text-xs px-3 py-1 rounded-full transition-colors"
      style={{
        color: active ? 'var(--amber)' : 'var(--text-muted)',
        background: active ? 'var(--amber-bg)' : 'transparent',
        border: `1px solid ${active ? 'var(--amber)' : 'var(--border)'}`,
      }}
    >
      {children}
    </button>
  )
}

export default function FilterBar({ category, difficulty, sort, onCategory, onDifficulty, onSort }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-4 mb-2">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: 'var(--text-muted)' }}>
          カテゴリ
        </span>
        <div className="flex gap-1.5">
          {CATEGORIES.map((c) => (
            <Pill key={c.value} active={category === c.value} onClick={() => onCategory(c.value)}>
              {c.label}
            </Pill>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: 'var(--text-muted)' }}>
          難易度
        </span>
        <div className="flex gap-1.5">
          {DIFFICULTIES.map((d) => (
            <Pill key={d.value} active={difficulty === d.value} onClick={() => onDifficulty(d.value)}>
              {d.label}
            </Pill>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2 ml-auto">
        <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: 'var(--text-muted)' }}>
          並び順
        </span>
        <select
          value={sort}
          onChange={(e) => onSort(e.target.value as SortOrder)}
          className="text-xs px-2.5 py-1 rounded transition-colors appearance-none pr-6"
          style={{
            color: 'var(--text-muted)',
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%23666'/%3E%3C/svg%3E")`,
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'right 8px center',
          }}
        >
          {SORT_OPTIONS.map((s) => (
            <option key={s.value} value={s.value} style={{ background: 'var(--bg)' }}>
              {s.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
