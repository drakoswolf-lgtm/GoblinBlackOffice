/**
 * GoblinPick — select an operative and their case type before creating a case.
 */

import { useState, useEffect } from 'react'
import { api } from '../api/client'

export default function GoblinPick({ onPicked, onCancel }) {
  const [goblins, setGoblins] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.listGoblins()
      .then(setGoblins)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handlePick = () => {
    if (!selected) return
    const caseType = selected.acceptedCaseTypes[0]
    onPicked(selected.id, caseType)
  }

  if (loading) return <div style={{ color: 'var(--text-muted)', padding: '2rem' }}><span className="spinner" /> Summoning operatives…</div>
  if (error) return <div className="error-box">Failed to load goblins: {error}</div>

  return (
    <div>
      <h2 style={{ marginBottom: '0.3rem' }}>Summon an Operative</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
        Select a goblin to handle your assignment.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', marginBottom: '1.5rem' }}>
        {goblins.map(g => (
          <div
            key={g.id}
            className="card"
            onClick={() => setSelected(g)}
            style={{
              cursor: 'pointer',
              border: selected?.id === g.id
                ? '2px solid var(--green-light)'
                : '1px solid var(--border)',
              transition: 'border-color 0.15s',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontWeight: 'bold', color: 'var(--text-strong)', fontSize: '1.05rem' }}>
                  🧌 {g.name}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {g.title} · {g.division}
                </div>
              </div>
              <StatusDot status={g.status} />
            </div>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: '0.7rem 0' }}>
              {g.flavor}
            </p>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {g.capabilities.map(cap => (
                <span key={cap} style={{
                  background: 'var(--surface2)',
                  border: '1px solid var(--border)',
                  borderRadius: 4,
                  padding: '2px 8px',
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                }}>
                  {cap.replace(/_/g, ' ')}
                </span>
              ))}
            </div>

            <div style={{ marginTop: '0.7rem', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Accepts: </span>
              {g.acceptedCaseTypes.map(t => (
                <span key={t} style={{ color: 'var(--green-light)' }}>
                  {t.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '0.7rem' }}>
        <button className="btn-primary" disabled={!selected} onClick={handlePick}>
          Assign Operative →
        </button>
        <button className="btn-secondary" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  )
}

function StatusDot({ status }) {
  const colors = { available: 'var(--green-light)', busy: 'var(--gold)', offline: 'var(--text-muted)' }
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.8rem', color: colors[status] }}>
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: colors[status], display: 'inline-block' }} />
      {status}
    </span>
  )
}
