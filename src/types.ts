export interface Idea {
  id: number
  title: string
  description: string
  target_market: string | null
  why_now: string | null
  revenue_model: string | null
  difficulty: 'low' | 'medium' | 'high'
  category: 'saas' | 'seo'
  generated_at: string
}

export interface ResearchItem {
  id: number
  source: string
  title: string
  url: string | null
  category: string
  score: number | null
  fetched_at: string
}
