interface Props {
  current: number
  total: number
  onChange: (page: number) => void
}

export default function Pagination({ current, total, onChange }: Props) {
  if (total <= 1) return null

  const pages: (number | '...')[] = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
      pages.push(i)
    }
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }

  const btnBase =
    'text-sm rounded-lg transition-colors border border-gray-200 dark:border-gray-700 dark:text-gray-300'

  return (
    <div className="flex items-center justify-center gap-1">
      <button
        onClick={() => onChange(current - 1)}
        disabled={current === 1}
        className={`${btnBase} px-3 py-1.5 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700`}
      >
        前へ
      </button>

      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`e${i}`} className="px-2 text-gray-400">…</span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p)}
            className={`w-9 h-9 ${btnBase} ${
              p === current
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            {p}
          </button>
        ),
      )}

      <button
        onClick={() => onChange(current + 1)}
        disabled={current === total}
        className={`${btnBase} px-3 py-1.5 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700`}
      >
        次へ
      </button>
    </div>
  )
}
