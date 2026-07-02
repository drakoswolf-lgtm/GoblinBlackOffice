/**
 * StageReview — user verifies/edits extracted data, approves, then generates.
 *
 * This is stage 3 of the canonical workflow.
 * Shows extracted values pre-filled, confidence meter, inline warnings,
 * and blocks generation until the user explicitly approves.
 */

import { useState } from 'react'
import { api } from '../api/client'
import ConfidenceMeter from './ConfidenceMeter'

export default function StageReview({ caseData, onUpdate }) {
  const ed = caseData.extractedData ?? {}
  const rd = caseData.reviewedData

  const [form, setForm] = useState({
    vendor:   rd?.vendor  ?? ed.vendor  ?? '',
    date:     rd?.date    ?? ed.date    ?? '',
    total:    rd?.total   ?? ed.total   ?? '',
    currency: rd?.currency ?? ed.currency ?? 'USD',
    purpose:  rd?.purpose ?? '',
    notes:    rd?.notes   ?? '',
    approved: rd?.approved ?? false,
  })
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [genError, setGenError] = useState(null)
  const [saved, setSaved] = useState(false)

  const set = (k, v) => { setForm(f => ({ ...f, [k]: v })); setSaved(false) }

  const handleSave = async () => {
    setSaveError(null)
    setSaving(true)
    try {
      await api.saveReview(caseData.id, {
        ...form,
        total: form.total !== '' ? parseFloat(form.total) : null,
      })
      setSaved(true)
      await onUpdate()
    } catch (e) {
      setSaveError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleGenerate = async () => {
    if (!form.approved) return
    setGenError(null)
    // Save first to ensure latest data is persisted
    setSaving(true)
    try {
      await api.saveReview(caseData.id, {
        ...form,
        total: form.total !== '' ? parseFloat(form.total) : null,
      })
    } catch (e) {
      setSaveError(e.message)
      setSaving(false)
      return
    }
    setSaving(false)

    setGenerating(true)
    try {
      await api.generate(caseData.id)
      await onUpdate()
    } catch (e) {
      setGenError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  const confidence = ed.confidence ?? 0

  return (
    <div>
      <h3 style={{ marginBottom: '0.3rem' }}>Review Extracted Data</h3>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
        Ledgergut has read your receipt. Verify each field before approving.
      </p>

      <ConfidenceMeter confidence={confidence} />

      {ed.warnings?.length > 0 && (
        <div className="warning-box" style={{ marginBottom: '1rem' }}>
          {ed.warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <Field label="Vendor">
          <input type="text" value={form.vendor} onChange={e => set('vendor', e.target.value)} placeholder="e.g. Coffee Palace" />
        </Field>
        <Field label="Date">
          <input type="text" value={form.date} onChange={e => set('date', e.target.value)} placeholder="e.g. 2024-03-15" />
        </Field>
        <Field label="Total">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input type="text" value={form.currency} onChange={e => set('currency', e.target.value)} style={{ width: 70, flex: 'none' }} placeholder="USD" />
            <input type="number" step="0.01" value={form.total} onChange={e => set('total', e.target.value)} placeholder="0.00" />
          </div>
        </Field>
        <Field label="Purpose">
          <input type="text" value={form.purpose} onChange={e => set('purpose', e.target.value)} placeholder="e.g. Team lunch, client meeting…" />
        </Field>
        <Field label="Notes">
          <textarea rows={2} value={form.notes} onChange={e => set('notes', e.target.value)} placeholder="Optional notes for approver" style={{ resize: 'vertical' }} />
        </Field>

        {/* Approval checkbox */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.7rem', marginTop: '0.5rem', paddingTop: '0.8rem', borderTop: '1px solid var(--border)' }}>
          <input
            id="approved"
            type="checkbox"
            checked={form.approved}
            onChange={e => set('approved', e.target.checked)}
            style={{ width: 'auto', accentColor: 'var(--green-light)', cursor: 'pointer' }}
          />
          <label htmlFor="approved" style={{ color: 'var(--text-strong)', cursor: 'pointer', userSelect: 'none' }}>
            I confirm the details above are correct and approve this claim.
          </label>
        </div>
      </div>

      {saveError && <div className="error-box" style={{ marginBottom: '0.8rem' }}>⚠ Save error: {saveError}</div>}
      {genError  && <div className="error-box" style={{ marginBottom: '0.8rem' }}>⚠ Generation failed: {genError}</div>}
      {saved     && <div className="success-box" style={{ marginBottom: '0.8rem' }}>✓ Changes saved.</div>}

      <div style={{ display: 'flex', gap: '0.7rem', flexWrap: 'wrap' }}>
        <button className="btn-secondary" disabled={saving} onClick={handleSave}>
          {saving ? <><span className="spinner" />Saving…</> : 'Save Changes'}
        </button>
        <button
          className="btn-gold"
          disabled={!form.approved || saving || generating}
          onClick={handleGenerate}
          style={{ minWidth: 200 }}
        >
          {generating
            ? <><span className="spinner" />Generating…</>
            : form.approved
              ? 'Generate Reimbursement Package →'
              : 'Approve above to generate'}
        </button>
      </div>
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
