import { useState, useEffect, useMemo } from 'react'
import type { Idea, ResearchItem, MeetingSession } from './types'
import FilterBar, { type SortOrder } from './components/FilterBar'
import IdeaCard from './components/IdeaCard'
import Pagination from './components/Pagination'
import ResearchTable from './components/ResearchTable'
import MeetingTab from './components/MeetingTab'

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

  const [activeTab, setActiveTab] = useState<'ideas' | 'research' | 'meeting'>('ideas')
  const [category, setCategory] = useState<CategoryFilter>('all')
  const [difficulty, setDifficulty] = useState<DifficultyFilter>('all')
  const [sort, setSort] = useState<SortOrder>('date_desc')
  const [ideasPage, setIdeasPage] = useState(1)
  const [researchPage, setResearchPage] = useState(1)

  const [dark, setDark] = useState(false)
  const [meetings, setMeetings] = useState<MeetingSession[]>([])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  useEffect(() => {
    Promise.all([
      fetch(`${BASE}data/ideas.json`),
      fetch(`${BASE}data/research.json`),
      fetch(`${BASE}data/meetings.json`).catch(() => null),
    ])
      .then(([r1, r2, r3]) =>
        Promise.all([r1.json(), r2.json(), r3 ? r3.json() : Promise.resolve(null)]),
      )
      .then(([ideasData, researchData, meetingsData]) => {
        setIdeas(ideasData.ideas ?? [])
        setResearch(researchData.items ?? [])
        setExportedAt(ideasData.exported_at ?? null)
        setMeetings(meetingsData?.sessions ?? [])
        setLoading(false)
      })
      .catch(() => {
        setError('データの読み込みに失敗しました。パイプラインを実行後にリロードしてください。')
        setLoading(false)
      })
  }, [])

  const DIFF_RANK: Record<string, number> = { low: 1, medium: 2, high: 3 }

  const filtered = useMemo(() => {
    const base = ideas.filter(
      (i) =>
        (category === 'all' || i.category === category) &&
        (difficulty === 'all' || i.difficulty === difficulty),
    )
    return [...base].sort((a, b) => {
      switch (sort) {
        case 'date_desc':
          return new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime()
        case 'date_asc':
          return new Date(a.generated_at).getTime() - new Date(b.generated_at).getTime()
        case 'diff_high':
          return (DIFF_RANK[b.difficulty] ?? 0) - (DIFF_RANK[a.difficulty] ?? 0)
        case 'diff_low':
          return (DIFF_RANK[a.difficulty] ?? 0) - (DIFF_RANK[b.difficulty] ?? 0)
        case 'score_high':
          return (b.eval_total ?? -1) - (a.eval_total ?? -1)
        case 'score_low':
          return (a.eval_total ?? Infinity) - (b.eval_total ?? Infinity)
        default:
          return 0
      }
    })
  }, [ideas, category, difficulty, sort])

  useEffect(() => setIdeasPage(1), [category, difficulty, sort])

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
          {(['ideas', 'research', 'meeting'] as const).map((tab) => {
            const label =
              tab === 'ideas'
                ? `アイデア (${filtered.length})`
                : tab === 'research'
                ? `リサーチ (${research.length})`
                : `会議 (${meetings.length})`
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
              sort={sort}
              onCategory={setCategory}
              onDifficulty={setDifficulty}
              onSort={setSort}
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

        {/* Meeting tab */}
        {activeTab === 'meeting' && (
          <section>
            <MeetingTab sessions={meetings} loading={loading} />
          </section>
        )}
      </main>
    </div>
  )
}
