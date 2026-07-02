/**
 * CaseFlow — the main 5-stage workflow page for a single case.
 *
 * Stages: intake → extraction → review → generation → completion → archived
 *
 * This component is the reference UI template: future goblins extend or
 * replace stage sub-components without changing the outer shell.
 */

import { useState, useEffect } from 'react'
import { api } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import StageIntake from '../components/StageIntake'
import StageReview from '../components/StageReview'
import StageComplete from '../components/StageComplete'

const STAGE_LABELS = {
  intake:     '1. Submit Evidence',
  extraction: '2. Extraction',
  review:     '3. Review Data',
  generation: '4. Generate Package',
  completion: '5. Complete',
  archived:   '✓ Archived',
  failed:     '✗ Failed',
}

export default function CaseFlow({ caseId, onDone }) {
  const [caseData, setCaseData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = async () => {
    try {
      const data = await api.getCase(caseId)
      setCaseData(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [caseId])

  if (loading) return <div style={{ padding: '2rem', color: 'var(--text-muted)' }}><span className="spinner" /> Loading case…</div>
  if (error)   return <div className="error-box">Error loading case: {error}</div>
  if (!caseData) return null

  const status = caseData.status

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.2rem' }}>
        <div>
          <h2 style={{ marginBottom: '0.2rem' }}>
            {formatCaseType(caseData.type)}
          </h2>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Case {caseData.id.slice(0, 8)} · Assigned to{' '}
            <span style={{ color: 'var(--green-light)' }}>{caseData.assignedGoblinId ?? 'unassigned'}</span>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Stage progress bar */}
      <StageProgress status={status} />

      {/* Status message */}
      <div style={{ margin: '1rem 0', padding: '0.6rem 1rem', background: 'var(--surface2)', borderRadius: 'var(--radius)', fontSize: '0.88rem' }}>
        {status === 'extraction' && <span className="spinner" />}
        {caseData.statusMessage}
      </div>

      {/* Warnings */}
      {caseData.warnings && caseData.warnings.length > 0 && (
        <div className="warning-box" style={{ marginBottom: '1rem' }}>
          {caseData.warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
        </div>
      )}

      {/* Stage-specific content */}
      {(status === 'intake' || status === 'failed') && (
        <StageIntake caseData={caseData} onUpdate={refresh} />
      )}
      {status === 'review' && (
        <StageReview caseData={caseData} onUpdate={refresh} />
      )}
      {(status === 'completion' || status === 'archived') && (
        <StageComplete caseData={caseData} onUpdate={refresh} onDone={onDone} />
      )}

      {/* Extraction in progress — auto-poll */}
      {status === 'extraction' && (
        <AutoPoll onDone={refresh} />
      )}
    </div>
  )
}

function AutoPoll({ onDone }) {
  useEffect(() => {
    const id = setTimeout(onDone, 1500)
    return () => clearTimeout(id)
  }, [])
  return null
}

const STAGES = ['intake', 'extraction', 'review', 'generation', 'completion', 'archived']

function StageProgress({ status }) {
  const idx = STAGES.indexOf(status)
  return (
    <div style={{ display: 'flex', gap: 4, marginBottom: '0.5rem' }}>
      {STAGES.map((s, i) => (
        <div
          key={s}
          title={STAGE_LABELS[s]}
          style={{
            flex: 1,
            height: 6,
            borderRadius: 3,
            background: status === 'failed'
              ? (i <= idx ? 'var(--red-light)' : 'var(--border)')
              : (i < idx ? 'var(--green)' : i === idx ? 'var(--green-light)' : 'var(--border)'),
            transition: 'background 0.3s',
          }}
        />
      ))}
    </div>
  )
}

function formatCaseType(type) {
  return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
