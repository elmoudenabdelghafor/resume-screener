import type { ScoreBreakdown } from '../types'

interface Props {
  score: number
  label?: keyof ScoreBreakdown
  size?: 'sm' | 'md' | 'lg'
  showBar?: boolean
}

function tier(score: number): string {
  if (score >= 75) return 'badge-high'
  if (score >= 50) return 'badge-mid'
  return 'badge-low'
}

export default function ScoreBadge({ score, label, size = 'md', showBar = false }: Props) {
  const cls = tier(score)
  const fontSz = size === 'lg' ? '1.1rem' : size === 'sm' ? '0.72rem' : '0.8rem'

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', gap: '0.3rem', width: showBar ? '100%' : 'auto' }}>
      {label && (
        <span style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>
          {label}
        </span>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span className={`badge ${cls}`} style={{ fontSize: fontSz }}>
          {Math.round(score)}
        </span>
        {showBar && (
          <div className="progress-bar" style={{ flex: 1 }}>
            <div className="progress-fill" style={{ width: `${score}%` }} />
          </div>
        )}
      </div>
    </div>
  )
}
