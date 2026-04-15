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

  return (
    <div className="flex items-center justify-center gap-1">
      <button
        onClick={() => onChange(current - 1)}
        disabled={current === 1}
        className="text-xs px-3 py-1.5 rounded transition-colors disabled:opacity-30"
        style={{ color: 'var(--text-sub)', border: '1px solid var(--border)' }}
      >
        前へ
      </button>

      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`e${i}`} className="px-2 text-xs" style={{ color: 'var(--text-muted)' }}>
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p)}
            className="w-8 h-8 text-xs rounded transition-colors"
            style={
              p === current
                ? { color: 'var(--amber)', background: 'var(--amber-bg)', border: '1px solid var(--amber)' }
                : { color: 'var(--text-sub)', border: '1px solid var(--border)' }
            }
          >
            {p}
          </button>
        ),
      )}

      <button
        onClick={() => onChange(current + 1)}
        disabled={current === total}
        className="text-xs px-3 py-1.5 rounded transition-colors disabled:opacity-30"
        style={{ color: 'var(--text-sub)', border: '1px solid var(--border)' }}
      >
        次へ
      </button>
    </div>
  )
}
