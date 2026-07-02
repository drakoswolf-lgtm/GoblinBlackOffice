/**
 * StageIntake — upload evidence files and trigger extraction.
 *
 * This is stage 1 of the canonical workflow.
 * Handles: drag-drop or click-to-upload, multiple files, extraction call,
 * and failure state reset (re-upload allowed when case is failed).
 */

import { useState } from 'react'
import { api } from '../api/client'

export default function StageIntake({ caseData, onUpdate }) {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [error, setError] = useState(null)
  const [dragOver, setDragOver] = useState(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = Array.from(e.dataTransfer.files)
    setFiles(prev => [...prev, ...dropped])
  }

  const handleFileInput = (e) => {
    setFiles(prev => [...prev, ...Array.from(e.target.files)])
    e.target.value = ''
  }

  const removeFile = (idx) => setFiles(prev => prev.filter((_, i) => i !== idx))

  const handleUploadAndExtract = async () => {
    if (!files.length) return
    setError(null)
    try {
      setUploading(true)
      await api.uploadEvidence(caseData.id, files)
      setUploading(false)

      setExtracting(true)
      await api.extract(caseData.id)
      await onUpdate()
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
      setExtracting(false)
    }
  }

  const busy = uploading || extracting
  const hasExisting = caseData.evidenceFiles?.length > 0
  const isFailed = caseData.status === 'failed'

  return (
    <div>
      <h3 style={{ marginBottom: '1rem' }}>Submit Evidence</h3>

      {isFailed && (
        <div className="error-box" style={{ marginBottom: '1rem' }}>
          Previous extraction failed. You may re-upload and try again.
        </div>
      )}

      {/* Existing uploaded files */}
      {hasExisting && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 4 }}>Already uploaded:</div>
          {caseData.evidenceFiles.map((f, i) => (
            <div key={i} style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>📎 {f.split('/').pop()}</div>
          ))}
        </div>
      )}

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        style={{
          border: `2px dashed ${dragOver ? 'var(--green-light)' : 'var(--border)'}`,
          borderRadius: 'var(--radius)',
          padding: '2rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'border-color 0.15s',
          marginBottom: '1rem',
          background: dragOver ? 'rgba(90,138,60,0.05)' : 'transparent',
        }}
        onClick={() => document.getElementById('file-input').click()}
      >
        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📄</div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Drag &amp; drop receipt here, or <span style={{ color: 'var(--green-light)' }}>click to browse</span>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: 4 }}>
          PDF, JPEG, PNG, or TXT accepted
        </div>
        <input
          id="file-input"
          type="file"
          multiple
          accept=".pdf,.jpg,.jpeg,.png,.gif,.txt,.csv"
          style={{ display: 'none' }}
          onChange={handleFileInput}
        />
      </div>

      {/* Selected file list */}
      {files.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          {files.map((f, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.3rem 0', borderBottom: '1px solid var(--border)', fontSize: '0.85rem' }}>
              <span>📎 {f.name} <span style={{ color: 'var(--text-muted)' }}>({formatBytes(f.size)})</span></span>
              <button className="btn-secondary" style={{ padding: '1px 8px', fontSize: '0.75rem' }} onClick={() => removeFile(i)}>×</button>
            </div>
          ))}
        </div>
      )}

      {error && <div className="error-box" style={{ marginBottom: '0.8rem' }}>⚠ {error}</div>}

      <button
        className="btn-primary"
        disabled={busy || (!files.length && !hasExisting)}
        onClick={handleUploadAndExtract}
        style={{ minWidth: 200 }}
      >
        {busy
          ? <><span className="spinner" />{uploading ? 'Uploading…' : 'Ledgergut is reading…'}</>
          : 'Submit to Ledgergut →'}
      </button>
    </div>
  )
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
