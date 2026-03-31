import { useLocation, useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import type { Candidate } from '../types'
import { getResults } from '../api'
import ScoreBadge from '../components/ScoreBadge'
import SkillTag from '../components/SkillTag'
import RadarChartBreakdown from '../components/RadarChartBreakdown'

export default function CandidateDetail() {
  const { jobId, resumeId } = useParams<{ jobId: string; resumeId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const [candidate, setCandidate] = useState<Candidate | null>(
    (location.state as Candidate) ?? null
  )
  const [loading, setLoading] = useState(!candidate)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (candidate) return
    if (!jobId || !resumeId) return
    
    getResults(jobId)
      .then(results => {
        const found = results.find(r => r.resume_id === resumeId)
        if (found) setCandidate(found)
        else setError('Candidate not found in results.')
      })
      .catch(() => setError('Failed to load candidate details.'))
      .finally(() => setLoading(false))
  }, [candidate, jobId, resumeId])

  if (loading) {
    return (
      <div className="flex-center" style={{ minHeight: '60vh', flexDirection: 'column', gap: '0.75rem' }}>
        <span className="animate-spin" style={{ fontSize: '1.5rem', display: 'block' }}>⟳</span>
        <span style={{ color: 'var(--text-secondary)' }}>Loading candidate…</span>
      </div>
    )
  }

  if (error || !candidate) {
    return (
      <div className="flex-center" style={{ minHeight: '60vh', flexDirection: 'column', gap: '1rem' }}>
        <span style={{ fontSize: '2.5rem' }}>⚠️</span>
        <p style={{ color: 'var(--danger)' }}>{error ?? 'Candidate not found.'}</p>
        <button className="btn btn-ghost" onClick={() => navigate('/jobs')}>← Back to results</button>
      </div>
    )
  }

  const { entities } = candidate

  return (
    <div className="animate-fade-up" style={{ maxWidth: 860, margin: '0 auto' }}>
      {/* Back link */}
      <button
        className="btn btn-ghost"
        style={{ marginBottom: '1.25rem', padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
        onClick={() => navigate('/jobs')}
      >
        ← Back to results
      </button>

      {/* Header card */}
      <div className="card-flat" style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'flex-start', gap: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>{candidate.filename}</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.4rem', lineHeight: 1.6, maxWidth: 520 }}>
            {candidate.summary}
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <code style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
              ID: {candidate.resume_id}
            </code>
          </div>
        </div>
        <div>
          <ScoreBadge score={candidate.overall_score} size="lg" />
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.3rem', textAlign: 'center' }}>
            overall
          </div>
        </div>
      </div>

      {/* Score breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.25rem' }} className="responsive-grid">
        {/* Radar chart */}
        <div className="card-flat">
          <h2 style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Score Breakdown
          </h2>
          <RadarChartBreakdown breakdown={candidate.breakdown} />
        </div>

        {/* Bar breakdown */}
        <div className="card-flat">
          <h2 style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
            Detailed Scores
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {(['skills', 'experience', 'education', 'overall'] as const).map(key => (
              <ScoreBadge
                key={key}
                score={candidate.breakdown[key]}
                label={key}
                showBar
              />
            ))}
          </div>
        </div>
      </div>

      {/* Entities */}
      <div className="card-flat">
        <h2 style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Extracted Entities
        </h2>

        {entities.companies.length > 0 && (
          <Section title="Companies">
            {entities.companies.map(c => <SkillTag key={c} label={c} variant="company" />)}
          </Section>
        )}
        {entities.degrees.length > 0 && (
          <Section title="Degrees">
            {entities.degrees.map(d => <SkillTag key={d} label={d} variant="degree" />)}
          </Section>
        )}
        {entities.tools.length > 0 && (
          <Section title="Tools & Technologies">
            {entities.tools.map(t => <SkillTag key={t} label={t} variant="tool" />)}
          </Section>
        )}
        {entities.locations.length > 0 && (
          <Section title="Locations">
            {entities.locations.map(l => <SkillTag key={l} label={l} variant="location" />)}
          </Section>
        )}
        {entities.misc.length > 0 && (
          <Section title="Other">
            {entities.misc.map(m => <SkillTag key={m} label={m} variant="misc" />)}
          </Section>
        )}

        {Object.values(entities).every(arr => arr.length === 0) && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No named entities were extracted from this resume.
          </p>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {title}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
        {children}
      </div>
    </div>
  )
}
