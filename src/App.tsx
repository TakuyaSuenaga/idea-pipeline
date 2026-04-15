import { useState, useEffect, useMemo } from 'react'
import type { Idea, ResearchItem } from './types'
import FilterBar from './components/FilterBar'
import IdeaCard from './components/IdeaCard'
import Pagination from './components/Pagination'
import ResearchTable from './components/ResearchTable'

const BASE = import.meta.env.BASE_URL
const IDEAS_PER_PAGE = 10
const RESEARCH_PER_PAGE = 30

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

  const [dark, setDark] = useState(false)

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
    <div>
      {/* Header */}
      <header
        className="sticky top-0 z-10 backdrop-blur-sm"
        style={{ background: 'rgba(10,10,15,0.85)', borderBottom: '1px solid var(--border)' }}
      >
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-sm font-semibold tracking-widest uppercase" style={{ color: 'var(--text-sub)' }}>
              Startup Idea Pipeline
            </h1>
            {exportedAt && (
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                更新 {new Date(exportedAt).toLocaleString('ja-JP')} — {ideas.length} 件
              </p>
            )}
          </div>
          <button
            onClick={() => setDark((d) => !d)}
            className="text-xs px-2.5 py-1 rounded transition-colors"
            style={{
              color: 'var(--text-muted)',
              border: '1px solid var(--border)',
            }}
          >
            {dark ? '☀' : '◑'}
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Tab bar */}
        <div className="flex gap-0 mb-8" style={{ borderBottom: '1px solid var(--border)' }}>
          {(['ideas', 'research'] as const).map((tab) => {
            const label =
              tab === 'ideas'
                ? `アイデア (${filtered.length})`
                : `リサーチ (${research.length})`
            const isActive = activeTab === tab
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className="px-4 py-3 text-sm font-medium transition-colors"
                style={{
                  color: isActive ? 'var(--amber)' : 'var(--text-muted)',
                  borderBottom: isActive ? '2px solid var(--amber)' : '2px solid transparent',
                  marginBottom: '-1px',
                }}
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
              <p className="text-center py-20 text-sm" style={{ color: 'var(--text-muted)' }}>
                読み込み中...
              </p>
            )}
            {error && (
              <p className="text-center py-20 text-sm" style={{ color: 'var(--diff-high)' }}>
                {error}
              </p>
            )}
            {!loading && !error && filtered.length === 0 && (
              <p className="text-center py-20 text-sm" style={{ color: 'var(--text-muted)' }}>
                条件に合うアイデアがありません。
              </p>
            )}
            {!loading && !error && filtered.length > 0 && (
              <>
                <ol className="mt-6" style={{ borderTop: '1px solid var(--border)' }}>
                  {pagedIdeas.map((idea, i) => (
                    <IdeaCard
                      key={idea.id}
                      idea={idea}
                      index={(ideasPage - 1) * IDEAS_PER_PAGE + i + 1}
                    />
                  ))}
                </ol>
                <div className="mt-8">
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
              <p className="text-center py-20 text-sm" style={{ color: 'var(--text-muted)' }}>
                読み込み中...
              </p>
            )}
            {!loading && (
              <>
                <ResearchTable items={pagedResearch} />
                <div className="mt-6">
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
