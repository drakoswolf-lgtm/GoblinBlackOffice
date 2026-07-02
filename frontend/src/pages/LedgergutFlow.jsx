/**
 * LedgergutFlow — standalone Ledgergut mock flow.
 *
 * Steps: Upload Receipt → Mock Extract → Review Fields → Generate Package → Success
 *
 * Uses the dedicated /ledgergut/* endpoints (no case model required).
 */

import { useState } from 'react'
import { api } from '../api/client'
import ConfidenceMeter from '../components/ConfidenceMeter'

const STEPS = ['upload', 'extracting', 'review', 'generating', 'success']

export default function LedgergutFlow({ onDone }) {
  const [step, setStep] = useState('upload')
  const [file, setFile] = useState(null)
  const [extracted, setExtracted] = useState(null)
  const [form, setForm] = useState({
    vendor: '', date: '', total: '', currency: 'USD', purpose: '', notes: '', approved: false,
  })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleExtract = async () => {
    if (!file) return
    setError(null)
    setStep('extracting')
    try {
      const data = await api.ledgergutExtract(file)
      setExtracted(data)
      setForm(f => ({
        ...f,
        vendor:   data.vendor   ?? '',
        date:     data.date     ?? '',
        total:    data.total    != null ? data.total : '',
        currency: data.currency ?? 'USD',
      }))
      setStep('review')
    } catch (e) {
      setError(e.message)
      setStep('upload')
    }
  }

  const handleGenerate = async () => {
    if (!form.approved) return
    setError(null)
    setStep('generating')
    try {
      const data = await api.ledgergutGenerate({
        vendor:   form.vendor   || null,
        date:     form.date     || null,
        total:    form.total !== '' ? parseFloat(form.total) : null,
        currency: form.currency || 'USD',
        purpose:  form.purpose  || null,
        notes:    form.notes    || null,
      })
      setResult(data)
      setStep('success')
    } catch (e) {
      setError(e.message)
      setStep('review')
    }
  }

  const setField = (k, v) => setForm(f => ({ ...f, [k]: v }))

  // ── Step: uploading ──────────────────────────────────────────────────────
  if (step === 'upload') {
    return (
      <UploadStep
        file={file}
        setFile={setFile}
        onSubmit={handleExtract}
        error={error}
      />
    )
  }

  // ── Step: extracting ─────────────────────────────────────────────────────
  if (step === 'extracting') {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🧾</div>
        <span className="spinner" />
        {' '}Ledgergut is reading your receipt…
      </div>
    )
  }

  // ── Step: review ─────────────────────────────────────────────────────────
  if (step === 'review') {
    return (
      <ReviewStep
        extracted={extracted}
        form={form}
        setField={setField}
        onGenerate={handleGenerate}
        error={error}
      />
    )
  }

  // ── Step: generating ─────────────────────────────────────────────────────
  if (step === 'generating') {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>📦</div>
        <span className="spinner" />
        {' '}Ledgergut is preparing your reimbursement package…
      </div>
    )
  }

  // ── Step: success ────────────────────────────────────────────────────────
  if (step === 'success') {
    return <SuccessStep result={result} form={form} onDone={onDone} />
  }

  return null
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function UploadStep({ file, setFile, onSubmit, error }) {
  const [dragOver, setDragOver] = useState(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  return (
    <div>
      <h3 style={{ marginBottom: '0.3rem' }}>Present Your Receipt</h3>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
        Upload a receipt and Ledgergut will extract the details for you.
      </p>

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => document.getElementById('lg-file-input').click()}
        style={{
          border: `2px dashed ${dragOver ? 'var(--green-light)' : 'var(--border)'}`,
          borderRadius: 'var(--radius)',
          padding: '2.5rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'border-color 0.15s',
          marginBottom: '1rem',
          background: dragOver ? 'rgba(90,138,60,0.05)' : 'transparent',
        }}
      >
        <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🧾</div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Drag &amp; drop your receipt, or{' '}
          <span style={{ color: 'var(--green-light)' }}>click to browse</span>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: 4 }}>
          PDF, JPEG, PNG, or TXT accepted
        </div>
        <input
          id="lg-file-input"
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.gif,.txt,.csv"
          style={{ display: 'none' }}
          onChange={e => {
            if (e.target.files[0]) setFile(e.target.files[0])
            e.target.value = ''
          }}
        />
      </div>

      {/* Selected file */}
      {file && (
        <div style={{ marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          📎 {file.name}{' '}
          <span style={{ color: 'var(--text-muted)' }}>({formatBytes(file.size)})</span>
          <button
            className="btn-secondary"
            style={{ marginLeft: '0.5rem', padding: '1px 8px', fontSize: '0.75rem' }}
            onClick={() => setFile(null)}
          >
            ×
          </button>
        </div>
      )}

      {error && (
        <div className="error-box" style={{ marginBottom: '0.8rem' }}>⚠ {error}</div>
      )}

      <button
        className="btn-primary"
        disabled={!file}
        onClick={onSubmit}
        style={{ minWidth: 220 }}
      >
        Submit to Ledgergut →
      </button>
    </div>
  )
}

function ReviewStep({ extracted, form, setField, onGenerate, error }) {
  const confidence = extracted?.confidence ?? 0

  return (
    <div>
      <h3 style={{ marginBottom: '0.3rem' }}>Review Extracted Fields</h3>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
        Ledgergut has read your receipt. Verify each field before approving.
      </p>

      <ConfidenceMeter confidence={confidence} />

      {extracted?.warnings?.length > 0 && (
        <div className="warning-box" style={{ marginBottom: '1rem' }}>
          {extracted.warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <Field label="Vendor">
          <input
            type="text"
            value={form.vendor}
            onChange={e => setField('vendor', e.target.value)}
            placeholder="e.g. Coffee Palace"
          />
        </Field>
        <Field label="Date">
          <input
            type="text"
            value={form.date}
            onChange={e => setField('date', e.target.value)}
            placeholder="e.g. 2024-03-15"
          />
        </Field>
        <Field label="Total">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              value={form.currency}
              onChange={e => setField('currency', e.target.value)}
              style={{ width: 70, flex: 'none' }}
              placeholder="USD"
            />
            <input
              type="number"
              step="0.01"
              value={form.total}
              onChange={e => setField('total', e.target.value)}
              placeholder="0.00"
            />
          </div>
        </Field>
        <Field label="Purpose">
          <input
            type="text"
            value={form.purpose}
            onChange={e => setField('purpose', e.target.value)}
            placeholder="e.g. Team lunch, client meeting…"
          />
        </Field>
        <Field label="Notes">
          <textarea
            rows={2}
            value={form.notes}
            onChange={e => setField('notes', e.target.value)}
            placeholder="Optional notes for approver"
            style={{ resize: 'vertical' }}
          />
        </Field>

        {/* Approval */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.7rem',
          marginTop: '0.5rem',
          paddingTop: '0.8rem',
          borderTop: '1px solid var(--border)',
        }}>
          <input
            id="lg-approved"
            type="checkbox"
            checked={form.approved}
            onChange={e => setField('approved', e.target.checked)}
            style={{ width: 'auto', accentColor: 'var(--green-light)', cursor: 'pointer' }}
          />
          <label htmlFor="lg-approved" style={{ color: 'var(--text-strong)', cursor: 'pointer', userSelect: 'none' }}>
            I confirm the details above are correct and approve this claim.
          </label>
        </div>
      </div>

      {error && (
        <div className="error-box" style={{ marginBottom: '0.8rem' }}>⚠ {error}</div>
      )}

      <button
        className="btn-gold"
        disabled={!form.approved}
        onClick={onGenerate}
        style={{ minWidth: 220 }}
      >
        {form.approved
          ? 'Generate Reimbursement Package →'
          : 'Approve above to generate'}
      </button>
    </div>
  )
}

function SuccessStep({ result, form, onDone }) {
  const downloadUrl = result ? api.ledgergutDownloadUrl(result.filename) : null

  return (
    <div>
      <div className="success-box" style={{ fontSize: '1rem', marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        ✓ Reimbursement package generated successfully!
      </div>

      {/* Summary */}
      <div className="card" style={{ marginBottom: '1.2rem' }}>
        <h3 style={{ marginBottom: '0.8rem' }}>Expense Summary</h3>
        <Row label="Vendor"  value={form.vendor  || '—'} />
        <Row label="Date"    value={form.date    || '—'} />
        <Row label="Amount"  value={`${form.currency} ${parseFloat(form.total || 0).toFixed(2)}`} />
        <Row label="Purpose" value={form.purpose || '—'} />
        {form.notes && <Row label="Notes" value={form.notes} />}
      </div>

      {/* Download */}
      {downloadUrl && (
        <div style={{ marginBottom: '1.2rem' }}>
          <a href={downloadUrl} download={result.filename}>
            <button className="btn-gold" style={{ fontSize: '1rem', padding: '0.6rem 1.5rem' }}>
              ⬇ Download Reimbursement Package
            </button>
          </a>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
            {result.filename}
          </div>
        </div>
      )}

      <button className="btn-primary" onClick={onDone}>← Back to Dashboard</button>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div className="field-row">
      <label className="field-label">{label}</label>
      {children}
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="field-row" style={{ marginBottom: '0.5rem' }}>
      <span className="field-label">{label}</span>
      <span style={{ color: 'var(--text-strong)' }}>{value}</span>
    </div>
  )
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
