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

const btnBase = 'px-3 py-1.5 text-sm transition-colors'
const btnActive = 'bg-indigo-600 text-white'
const btnInactive =
  'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'

export default function FilterBar({ category, difficulty, onCategory, onDifficulty }: Props) {
  return (
    <div className="flex flex-wrap gap-4">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500 dark:text-gray-400">カテゴリ</span>
        <div className="flex rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              onClick={() => onCategory(c.value)}
              className={`${btnBase} ${category === c.value ? btnActive : btnInactive}`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500 dark:text-gray-400">難易度</span>
        <div className="flex rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
          {DIFFICULTIES.map((d) => (
            <button
              key={d.value}
              onClick={() => onDifficulty(d.value)}
              className={`${btnBase} ${difficulty === d.value ? btnActive : btnInactive}`}
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
