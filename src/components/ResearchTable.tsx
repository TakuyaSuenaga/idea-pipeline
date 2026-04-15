import type { ResearchItem } from '../types'

const CATEGORY_STYLES: Record<string, string> = {
  saas: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  seo: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  general: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200',
}

interface Props {
  items: ResearchItem[]
}

export default function ResearchTable({ items }: Props) {
  if (items.length === 0) {
    return (
      <p className="text-center text-gray-500 dark:text-gray-400 py-8">
        リサーチデータがありません。
      </p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
          <tr>
            <th className="text-left px-4 py-3 font-medium whitespace-nowrap">ソース</th>
            <th className="text-left px-4 py-3 font-medium">タイトル</th>
            <th className="text-left px-4 py-3 font-medium whitespace-nowrap">カテゴリ</th>
            <th className="text-left px-4 py-3 font-medium whitespace-nowrap">スコア</th>
            <th className="text-left px-4 py-3 font-medium whitespace-nowrap">取得日</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
          {items.map((item) => (
            <tr
              key={item.id}
              className="bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <td className="px-4 py-3 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                {item.source}
              </td>
              <td className="px-4 py-3 text-gray-900 dark:text-gray-100 max-w-xs">
                {item.url ? (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-600 dark:text-indigo-400 hover:underline line-clamp-2"
                  >
                    {item.title}
                  </a>
                ) : (
                  <span className="line-clamp-2">{item.title}</span>
                )}
              </td>
              <td className="px-4 py-3">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    CATEGORY_STYLES[item.category] ?? CATEGORY_STYLES.general
                  }`}
                >
                  {item.category}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                {item.score ?? '—'}
              </td>
              <td className="px-4 py-3 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                {new Date(item.fetched_at).toLocaleDateString('ja-JP')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
