import { useState } from 'react'
import type { MeetingSession, MeetingMessage } from '../types'

const ROLE_LABELS: Record<string, string> = {
  ceo: 'CEO',
  planning: '企画担当',
  sales: '営業担当',
  marketing: 'マーケティング担当',
  dev: '開発担当',
  ops: '運用担当',
}

function roleBorderColor(role: string): string {
  switch (role) {
    case 'ceo':
      return 'var(--amber)'
    case 'planning':
      return 'var(--diff-low)'
    case 'sales':
      return '#60a5fa'
    case 'marketing':
      return '#c084fc'
    case 'dev':
      return '#34d399'
    case 'ops':
      return '#fb923c'
    default:
      return 'var(--border)'
  }
}

function MessageRow({ msg }: { msg: MeetingMessage }) {
  const label = ROLE_LABELS[msg.agent_role] ?? msg.agent_role
  const color = roleBorderColor(msg.agent_role)
  return (
    <div
      className="border-l-2 pl-4 py-2"
      style={{ borderColor: color, marginBottom: '0.75rem' }}
    >
      <p
        className="text-[10px] font-bold uppercase tracking-widest mb-1"
        style={{ color }}
      >
        {label}
      </p>
      <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--text-sub)' }}>
        {msg.content}
      </p>
    </div>
  )
}

function SessionRow({ session, index }: { session: MeetingSession; index: number }) {
  const [expanded, setExpanded] = useState(false)

  const isAdopted = session.conclusion === '採用'
  const conclusionColor = isAdopted ? 'var(--diff-low)' : 'var(--text-muted)'
  const date = new Date(session.held_at).toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
  })

  return (
    <li style={{ borderBottom: '1px solid var(--border)' }}>
      <button
        className="w-full text-left flex items-start gap-4 py-5 group"
        onClick={() => setExpanded((e) => !e)}
      >
        <span
          className="text-xs font-mono tabular-nums mt-0.5 shrink-0 w-6 text-right"
          style={{ color: 'var(--text-muted)' }}
        >
          {String(index).padStart(2, '0')}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2 flex-wrap">
            <h3
              className="font-medium text-[15px] leading-snug flex-1 min-w-0 group-hover:opacity-80 transition-opacity"
              style={{ color: 'var(--text)' }}
            >
              {session.idea_title}
            </h3>
            <div className="flex items-center gap-2 shrink-0 mt-0.5">
              {session.conclusion && (
                <span
                  className="text-[10px] px-1.5 py-0.5 font-semibold rounded tracking-wide"
                  style={{
                    color: conclusionColor,
                    border: `1px solid ${conclusionColor}`,
                  }}
                >
                  {session.conclusion}
                </span>
              )}
              <time className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                {date}
              </time>
              <span
                className="text-xs transition-transform duration-200"
                style={{
                  color: 'var(--text-muted)',
                  display: 'inline-block',
                  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                }}
              >
                ▾
              </span>
            </div>
          </div>
          <p className="text-sm mt-1 tabular-nums" style={{ color: 'var(--text-muted)' }}>
            発言 {session.messages.length} 件
          </p>
        </div>
      </button>

      {expanded && (
        <div className="pl-10 pb-5">
          {session.github_issue_url && (
            <a
              href={session.github_issue_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs inline-flex items-center gap-1 mb-4 transition-opacity hover:opacity-70"
              style={{ color: 'var(--amber)' }}
            >
              GitHub Issue →
            </a>
          )}
          <div>
            {session.messages.map((msg) => (
              <MessageRow key={msg.turn} msg={msg} />
            ))}
          </div>
        </div>
      )}
    </li>
  )
}

interface Props {
  sessions: MeetingSession[]
  loading: boolean
}

export default function MeetingTab({ sessions, loading }: Props) {
  if (loading) {
    return (
      <p className="text-center py-20 text-sm" style={{ color: 'var(--text-muted)' }}>
        読み込み中...
      </p>
    )
  }

  if (sessions.length === 0) {
    return (
      <p className="text-center py-20 text-sm" style={{ color: 'var(--text-muted)' }}>
        まだ会議の記録がありません。
      </p>
    )
  }

  return (
    <ol style={{ borderTop: '1px solid var(--border)' }}>
      {sessions.map((session, i) => (
        <SessionRow key={session.id} session={session} index={i + 1} />
      ))}
    </ol>
  )
}
