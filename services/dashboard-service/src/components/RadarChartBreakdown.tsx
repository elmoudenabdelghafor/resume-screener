import {
  Radar,
  RadarChart as ReRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { ScoreBreakdown } from '../types'

interface Props {
  breakdown: ScoreBreakdown
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ value: number }>
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-bright)',
      borderRadius: 'var(--radius-sm)',
      padding: '0.4rem 0.8rem',
      fontSize: '0.85rem',
      fontWeight: 600,
      color: 'var(--text-primary)',
    }}>
      {Math.round(payload[0].value)} / 100
    </div>
  )
}

export default function RadarChartBreakdown({ breakdown }: Props) {
  const data = [
    { subject: 'Skills',     value: breakdown.skills },
    { subject: 'Experience', value: breakdown.experience },
    { subject: 'Education',  value: breakdown.education },
    { subject: 'Overall',    value: breakdown.overall },
  ]

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ReRadarChart data={data} margin={{ top: 16, right: 24, bottom: 16, left: 24 }}>
        <PolarGrid stroke="rgba(99,102,241,0.15)" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: 'var(--text-secondary)', fontSize: 12, fontWeight: 600 }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tickCount={5}
          tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
        />
        <Radar
          name="Score"
          dataKey="value"
          stroke="#6366f1"
          fill="#6366f1"
          fillOpacity={0.25}
          strokeWidth={2}
        />
        <Tooltip content={<CustomTooltip />} />
      </ReRadarChart>
    </ResponsiveContainer>
  )
}
