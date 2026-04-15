type CategoryFilter = 'all' | 'saas' | 'seo'
type DifficultyFilter = 'all' | 'low' | 'medium' | 'high'

interface Props {
  category: CategoryFilter
  difficulty: DifficultyFilter
  onCategory: (c: CategoryFilter) => void
  onDifficulty: (d: DifficultyFilter) => void
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

export default function FilterBar({ category, difficulty, onCategory, onDifficulty }: Props) {
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
    </div>
  )
}
