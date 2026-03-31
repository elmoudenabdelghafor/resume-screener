import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadResumes } from '../api'

interface JobEntry {
  jobId: string
  filename: string
  status: 'uploading' | 'done' | 'error'
}

export default function Upload() {
  const navigate = useNavigate()
  const [jobDescription, setJobDescription] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState(false)
  const [entries, setEntries] = useState<JobEntry[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const addFiles = useCallback((incoming: FileList | null) => {
    if (!incoming) return
    const allowed = Array.from(incoming).filter(f =>
      f.type === 'application/pdf' ||
      f.name.endsWith('.docx') ||
      f.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name))
      return [...prev, ...allowed.filter(f => !names.has(f.name))]
    })
  }, [])

  const removeFile = (name: string) => setFiles(prev => prev.filter(f => f.name !== name))

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false)
    addFiles(e.dataTransfer.files)
  }

  const handleSubmit = async () => {
    if (!jobDescription.trim()) { setError('Please enter a job description.'); return }
    if (files.length === 0) { setError('Please add at least one resume file.'); return }
    setError(null); setBusy(true)

    const pending: JobEntry[] = files.map(f => ({ jobId: '', filename: f.name, status: 'uploading' }))
    setEntries(pending)

    try {
      const results = await uploadResumes(files, jobDescription)
      const updated: JobEntry[] = results.map((r, i) => ({
        jobId: r.job_id,
        filename: files[i].name,
        status: 'done',
      }))
      setEntries(updated)
      // Save job IDs to localStorage so CandidateList can find them
      const existing = JSON.parse(localStorage.getItem('rs_jobs') ?? '[]')
      const newJobs = results.map((r, i) => ({
        job_id: r.job_id,
        filename: files[i].name,
        job_description: jobDescription,
        uploaded_at: new Date().toISOString(),
      }))
      localStorage.setItem('rs_jobs', JSON.stringify([...newJobs, ...existing]))
      setTimeout(() => navigate('/jobs'), 1500)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setError(msg)
      setEntries(prev => prev.map(e => ({ ...e, status: 'error' })))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="animate-fade-up" style={{ maxWidth: 640, margin: '0 auto' }}>
      <h1 className="section-title">
        Screen <span className="text-gradient">Resumes</span>
      </h1>
      <p className="section-sub">
        Upload PDF or DOCX resumes and let the AI rank candidates against your job description.
      </p>

      {/* Job description */}
      <div className="card-flat" style={{ marginBottom: '1.25rem' }}>
        <label className="form-label">Job Description</label>
        <textarea
          className="form-textarea"
          rows={5}
          placeholder="Paste the full job description here — the more detail, the better the scoring…"
          value={jobDescription}
          onChange={e => setJobDescription(e.target.value)}
        />
      </div>

      {/* Drop zone */}
      <div
        className={`upload-zone${dragging ? ' drag-over' : ''}`}
        style={{ marginBottom: '1rem' }}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,application/pdf"
          multiple
          style={{ display: 'none' }}
          onChange={e => addFiles(e.target.files)}
        />
        <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📂</div>
        <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          {dragging ? 'Drop files here' : 'Drag & drop resumes, or click to browse'}
        </p>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
          Supports PDF and DOCX
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="card-flat" style={{ marginBottom: '1.25rem' }}>
          {files.map(f => (
            <div key={f.name} style={{
              display: 'flex', alignItems: 'center', gap: '0.75rem',
              padding: '0.5rem 0', borderBottom: '1px solid var(--border)',
            }}>
              <span style={{ fontSize: '1.1rem' }}>📄</span>
              <span style={{ flex: 1, fontSize: '0.875rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {f.name}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {(f.size / 1024).toFixed(1)} KB
              </span>
              <button
                onClick={e => { e.stopPropagation(); removeFile(f.name) }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger)', fontSize: '1rem' }}
                title="Remove"
              >✕</button>
            </div>
          ))}
        </div>
      )}

      {/* Status entries after submit */}
      {entries.length > 0 && (
        <div style={{ marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {entries.map(e => (
            <div key={e.filename} style={{
              display: 'flex', alignItems: 'center', gap: '0.75rem',
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-sm)',
              background: e.status === 'done'
                ? 'rgba(16,185,129,0.1)'
                : e.status === 'error'
                ? 'rgba(239,68,68,0.1)'
                : 'rgba(99,102,241,0.1)',
              fontSize: '0.85rem',
            }}>
              <span>{e.status === 'done' ? '✅' : e.status === 'error' ? '❌' : '⏳'}</span>
              <span style={{ flex: 1 }}>{e.filename}</span>
              {e.jobId && (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                  {e.jobId.slice(0, 8)}…
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {error && (
        <p style={{ color: 'var(--danger)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>⚠ {error}</p>
      )}

      <button
        className="btn btn-primary"
        style={{ width: '100%', justifyContent: 'center', padding: '0.8rem' }}
        onClick={handleSubmit}
        disabled={busy}
      >
        {busy
          ? <><span className="animate-spin" style={{ display: 'inline-block' }}>⟳</span> Uploading…</>
          : '🚀 Screen Candidates'
        }
      </button>
    </div>
  )
}
