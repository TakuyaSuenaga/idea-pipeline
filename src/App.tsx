import { useState, useEffect, useMemo } from 'react'
import type { Idea, ResearchItem } from './types'
import FilterBar from './components/FilterBar'
import IdeaCard from './components/IdeaCard'
import Pagination from './components/Pagination'
import ResearchTable from './components/ResearchTable'

const BASE = import.meta.env.BASE_URL
const IDEAS_PER_PAGE = 12
const RESEARCH_PER_PAGE = 20

type CategoryFilter = 'all' | 'saas' | 'seo'
type DifficultyFilter = 'all' | 'low' | 'medium' | 'high'

export default function App() {
  const [ideas, setIdeas] = useState<Idea[]>([])
  const [research, setResearch] = useState<ResearchItem[]>([])
  const [exportedAt, setExportedAt] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [activeTab, setActiveTab] = useState<'ideas' | 'research'>('ideas')
  const [category, setCategory] = useState<CategoryFilter>('all')
  const [difficulty, setDifficulty] = useState<DifficultyFilter>('all')
  const [ideasPage, setIdeasPage] = useState(1)
  const [researchPage, setResearchPage] = useState(1)

  const [dark, setDark] = useState(
    () => window.matchMedia('(prefers-color-scheme: dark)').matches,
  )

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  useEffect(() => {
    Promise.all([
      fetch(`${BASE}data/ideas.json`),
      fetch(`${BASE}data/research.json`),
    ])
      .then(([r1, r2]) => Promise.all([r1.json(), r2.json()]))
      .then(([ideasData, researchData]) => {
        setIdeas(ideasData.ideas ?? [])
        setResearch(researchData.items ?? [])
        setExportedAt(ideasData.exported_at ?? null)
        setLoading(false)
      })
      .catch(() => {
        setError('データの読み込みに失敗しました。パイプラインを実行後にリロードしてください。')
        setLoading(false)
      })
  }, [])

  const filtered = useMemo(
    () =>
      ideas.filter(
        (i) =>
          (category === 'all' || i.category === category) &&
          (difficulty === 'all' || i.difficulty === difficulty),
      ),
    [ideas, category, difficulty],
  )

  useEffect(() => setIdeasPage(1), [category, difficulty])

  const totalIdeasPages = Math.max(1, Math.ceil(filtered.length / IDEAS_PER_PAGE))
  const pagedIdeas = filtered.slice(
    (ideasPage - 1) * IDEAS_PER_PAGE,
    ideasPage * IDEAS_PER_PAGE,
  )

  const totalResearchPages = Math.max(1, Math.ceil(research.length / RESEARCH_PER_PAGE))
  const pagedResearch = research.slice(
    (researchPage - 1) * RESEARCH_PER_PAGE,
    researchPage * RESEARCH_PER_PAGE,
  )

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              Startup Idea Pipeline
            </h1>
            {exportedAt && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                最終更新: {new Date(exportedAt).toLocaleString('ja-JP')} — {ideas.length}件
              </p>
            )}
          </div>
          <button
            onClick={() => setDark((d) => !d)}
            className="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            {dark ? 'ライト' : 'ダーク'}
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Tab bar */}
        <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6">
          {(['ideas', 'research'] as const).map((tab) => {
            const label = tab === 'ideas'
              ? `アイデア一覧 (${filtered.length})`
              : `リサーチソース (${research.length})`
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                }`}
              >
                {label}
              </button>
            )
          })}
        </div>

        {/* Ideas tab */}
        {activeTab === 'ideas' && (
          <section>
            <FilterBar
              category={category}
              difficulty={difficulty}
              onCategory={setCategory}
              onDifficulty={setDifficulty}
            />

            {loading && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-20">読み込み中...</p>
            )}
            {error && <p className="text-center text-red-500 py-20">{error}</p>}
            {!loading && !error && filtered.length === 0 && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-20">
                条件に合うアイデアがありません。
              </p>
            )}
            {!loading && !error && filtered.length > 0 && (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                  {pagedIdeas.map((idea) => (
                    <IdeaCard key={idea.id} idea={idea} />
                  ))}
                </div>
                <div className="mt-6">
                  <Pagination current={ideasPage} total={totalIdeasPages} onChange={setIdeasPage} />
                </div>
              </>
            )}
          </section>
        )}

        {/* Research tab */}
        {activeTab === 'research' && (
          <section>
            {loading && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-20">読み込み中...</p>
            )}
            {!loading && (
              <>
                <ResearchTable items={pagedResearch} />
                <div className="mt-4">
                  <Pagination
                    current={researchPage}
                    total={totalResearchPages}
                    onChange={setResearchPage}
                  />
                </div>
              </>
            )}
          </section>
        )}
      </main>
    </div>
  )
}
