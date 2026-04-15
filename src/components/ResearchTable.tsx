import type { ResearchItem } from '../types'

interface Props {
  items: ResearchItem[]
}

export default function ResearchTable({ items }: Props) {
  if (items.length === 0) {
    return (
      <p className="text-center py-8 text-sm" style={{ color: 'var(--text-muted)' }}>
        リサーチデータがありません。
      </p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg" style={{ border: '1px solid var(--border)' }}>
      <table className="w-full text-sm">
        <thead style={{ background: 'var(--elevated)' }}>
          <tr>
            {['ソース', 'タイトル', 'カテゴリ', 'スコア', '取得日'].map((h) => (
              <th
                key={h}
                className="text-left px-4 py-3 text-[10px] font-bold uppercase tracking-widest whitespace-nowrap"
                style={{ color: 'var(--text-muted)' }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item, i) => (
            <tr
              key={item.id}
              style={{
                background: i % 2 === 0 ? 'var(--surface)' : 'transparent',
                borderTop: '1px solid var(--border)',
              }}
            >
              <td className="px-4 py-3 text-xs whitespace-nowrap" style={{ color: 'var(--text-muted)' }}>
                {item.source}
              </td>
              <td className="px-4 py-3 max-w-xs">
                {item.url ? (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm hover:underline line-clamp-2"
                    style={{ color: 'var(--indigo)' }}
                  >
                    {item.title}
                  </a>
                ) : (
                  <span className="text-sm line-clamp-2" style={{ color: 'var(--text-sub)' }}>
                    {item.title}
                  </span>
                )}
              </td>
              <td className="px-4 py-3">
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded font-semibold tracking-wide"
                  style={
                    item.category === 'saas'
                      ? { color: 'var(--saas-fg)', background: 'var(--saas-bg)' }
                      : item.category === 'seo'
                        ? { color: 'var(--seo-fg)', background: 'var(--seo-bg)' }
                        : { color: 'var(--text-muted)', background: 'var(--elevated)' }
                  }
                >
                  {item.category}
                </span>
              </td>
              <td className="px-4 py-3 text-sm tabular-nums" style={{ color: 'var(--text-muted)' }}>
                {item.score ?? '—'}
              </td>
              <td className="px-4 py-3 text-xs whitespace-nowrap" style={{ color: 'var(--text-muted)' }}>
                {new Date(item.fetched_at).toLocaleDateString('ja-JP')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
