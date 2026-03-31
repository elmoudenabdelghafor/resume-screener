import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getResults } from '../api'
import type { Candidate } from '../types'
import ScoreBadge from '../components/ScoreBadge'

interface StoredJob {
  job_id: string
  filename: string
  job_description: string
  uploaded_at: string
}

interface Row extends Candidate {
  jobId: string
}

function medalFor(rank: number) {
  if (rank === 1) return '🥇'
  if (rank === 2) return '🥈'
  if (rank === 3) return '🥉'
  return `#${rank}`
}

export default function CandidateList() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState<StoredJob[]>([])
  const [selectedJob, setSelectedJob] = useState<StoredJob | null>(null)
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const stored: StoredJob[] = JSON.parse(localStorage.getItem('rs_jobs') ?? '[]')
    setJobs(stored)
    if (stored.length > 0) setSelectedJob(stored[0])
  }, [])

  const fetchResults = useCallback(async (job: StoredJob) => {
    setLoading(true); setError(null); setRows([])
    try {
      const candidates = await getResults(job.job_id)
      setRows(candidates.map(c => ({ ...c, jobId: job.job_id })))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load results'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedJob) fetchResults(selectedJob)
  }, [selectedJob, fetchResults])

  if (jobs.length === 0) {
    return (
      <div className="flex-center" style={{ flexDirection: 'column', gap: '1rem', minHeight: '60vh' }}>
        <div style={{ fontSize: '3rem' }}>📭</div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>No jobs yet.</p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          Upload Resumes
        </button>
      </div>
    )
  }

  return (
    <div className="animate-fade-up">
      <h1 className="section-title">
        Candidate <span className="text-gradient">Results</span>
      </h1>
      <p className="section-sub">Ranked by AI score against the job description.</p>

      {/* Job switcher */}
      {jobs.length > 1 && (
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
          {jobs.map(j => (
            <button
              key={j.job_id}
              className={`btn ${selectedJob?.job_id === j.job_id ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setSelectedJob(j)}
            >
              {j.filename || j.job_id.slice(0, 8)}
            </button>
          ))}
        </div>
      )}

      {/* Selected job info */}
      {selectedJob && (
        <div className="card-flat" style={{ marginBottom: '1.25rem', padding: '1rem 1.25rem' }}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'baseline', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)' }}>
              Job ID
            </span>
            <code style={{ fontSize: '0.8rem', color: 'var(--accent)' }}>{selectedJob.job_id}</code>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
              {new Date(selectedJob.uploaded_at).toLocaleString()}
            </span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.4rem', lineHeight: 1.5 }}>
            {selectedJob.job_description.slice(0, 200)}{selectedJob.job_description.length > 200 ? '…' : ''}
          </p>
        </div>
      )}

      {/* Table */}
      <div className="card-flat" style={{ padding: 0, overflow: 'hidden' }}>
        {loading && (
          <div className="flex-center" style={{ padding: '3rem', flexDirection: 'column', gap: '0.75rem' }}>
            <span className="animate-spin" style={{ fontSize: '1.5rem', display: 'block' }}>⟳</span>
            <span style={{ color: 'var(--text-secondary)' }}>Loading results…</span>
          </div>
        )}

        {error && (
          <div className="flex-center" style={{ padding: '3rem', flexDirection: 'column', gap: '0.5rem' }}>
            <span style={{ fontSize: '2rem' }}>⚠️</span>
            <p style={{ color: 'var(--danger)' }}>{error}</p>
            <button className="btn btn-ghost" onClick={() => selectedJob && fetchResults(selectedJob)}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && rows.length === 0 && (
          <div className="flex-center" style={{ padding: '3rem', flexDirection: 'column', gap: '0.5rem' }}>
            <span style={{ fontSize: '2rem' }}>🕐</span>
            <p style={{ color: 'var(--text-secondary)' }}>Still processing… give it a moment and reload.</p>
            <button className="btn btn-ghost" onClick={() => selectedJob && fetchResults(selectedJob)}>
              ↺ Reload
            </button>
          </div>
        )}

        {!loading && rows.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 60, textAlign: 'center' }}>Rank</th>
                <th>Candidate</th>
                <th style={{ width: 90 }}>Skills</th>
                <th style={{ width: 90 }}>Exp.</th>
                <th style={{ width: 90 }}>Education</th>
                <th style={{ width: 100 }}>Overall</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr
                  key={row.resume_id}
                  onClick={() => navigate(`/jobs/${row.jobId}/${row.resume_id}`, { state: row })}
                >
                  <td style={{ textAlign: 'center', fontSize: idx < 3 ? '1.2rem' : '0.875rem', fontWeight: 700 }}
                    className={idx === 0 ? 'rank-1' : idx === 1 ? 'rank-2' : idx === 2 ? 'rank-3' : ''}>
                    {medalFor(idx + 1)}
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{row.filename}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.2rem', lineHeight: 1.4 }}>
                      {row.summary}
                    </div>
                  </td>
                  <td><ScoreBadge score={row.breakdown.skills} /></td>
                  <td><ScoreBadge score={row.breakdown.experience} /></td>
                  <td><ScoreBadge score={row.breakdown.education} /></td>
                  <td><ScoreBadge score={row.overall_score} size="lg" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
