/**
 * StageComplete — success screen showing the generated package + export/archive.
 *
 * This is stage 5 of the canonical workflow.
 */

import { useState } from 'react'
import { api } from '../api/client'

export default function StageComplete({ caseData, onUpdate, onDone }) {
  const [archiving, setArchiving] = useState(false)
  const [error, setError] = useState(null)

  const rd = caseData.reviewedData ?? {}
  const ed = caseData.extractedData ?? {}
  const isArchived = caseData.status === 'archived'

  const handleArchive = async () => {
    setArchiving(true)
    setError(null)
    try {
      await api.archive(caseData.id)
      await onUpdate()
    } catch (e) {
      setError(e.message)
    } finally {
      setArchiving(false)
    }
  }

  const outputFile = caseData.outputFiles?.[0]
  const filename = outputFile ? outputFile.split('/').pop() : null
  const downloadUrl = filename ? api.downloadUrl(caseData.id, filename) : null

  return (
    <div>
      <div className="success-box" style={{ fontSize: '1rem', marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        {isArchived
          ? '✓ Case archived. Ledgergut has filed this one away.'
          : '✓ Reimbursement package generated successfully!'}
      </div>

      {/* Summary card */}
      <div className="card" style={{ marginBottom: '1.2rem' }}>
        <h3 style={{ marginBottom: '0.8rem' }}>Expense Summary</h3>
        <Row label="Vendor"   value={rd.vendor   || ed.vendor   || '—'} />
        <Row label="Date"     value={rd.date     || ed.date     || '—'} />
        <Row label="Amount"   value={formatAmount(rd, ed)} />
        <Row label="Purpose"  value={rd.purpose  || '—'} />
        {rd.notes && <Row label="Notes" value={rd.notes} />}
      </div>

      {/* Download */}
      {downloadUrl && (
        <div style={{ marginBottom: '1.2rem' }}>
          <a href={downloadUrl} download={filename}>
            <button className="btn-gold" style={{ fontSize: '1rem', padding: '0.6rem 1.5rem' }}>
              ⬇ Download Reimbursement Package
            </button>
          </a>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
            {filename}
          </div>
        </div>
      )}

      {error && <div className="error-box" style={{ marginBottom: '0.8rem' }}>⚠ {error}</div>}

      <div style={{ display: 'flex', gap: '0.7rem', flexWrap: 'wrap' }}>
        {!isArchived && (
          <button className="btn-secondary" disabled={archiving} onClick={handleArchive}>
            {archiving ? <><span className="spinner" />Archiving…</> : '🗄 Archive Case'}
          </button>
        )}
        <button className="btn-primary" onClick={onDone}>
          ← Back to Dashboard
        </button>
      </div>
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

function formatAmount(rd, ed) {
  const total    = rd.total    ?? ed.total
  const currency = rd.currency ?? ed.currency ?? 'USD'
  if (total == null) return '—'
  return `${currency} ${parseFloat(total).toFixed(2)}`
}
