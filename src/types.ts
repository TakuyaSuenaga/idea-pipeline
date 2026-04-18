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
  eval_why_now: number | null
  eval_differentiation: number | null
  eval_feasibility: number | null
  eval_market_size: number | null
  eval_pain_point: number | null
  eval_comment: string | null
  eval_total: number | null
}

export interface MeetingMessage {
  agent_role: 'ceo' | 'planning' | 'sales' | 'marketing' | 'dev' | 'ops'
  turn: number
  content: string
  created_at: string
}

export interface MeetingSession {
  id: number
  idea_id: number
  idea_title: string
  held_at: string
  conclusion: '採用' | '見送り' | null
  github_issue_url: string | null
  messages: MeetingMessage[]
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
