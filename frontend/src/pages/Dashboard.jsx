/**
 * Dashboard — lists all cases with status badges and quick-open links.
 */

import { api } from '../api/client'
import StatusBadge from '../components/StatusBadge'

export default function Dashboard({ cases, error, onOpen, onNew, onRefresh }) {
  if (error) {
    return (
      <div className="error-box" style={{ marginTop: '2rem' }}>
        ⚠ Could not connect to Goblin Black Office backend: {error}
        <div style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
          Make sure the API is running at <code>http://localhost:8000</code>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2>Active Cases</h2>
        <button className="btn-secondary" onClick={onRefresh}>↻ Refresh</button>
      </div>

      {cases.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🧌</div>
          <p>No cases on file. The goblins are restless.</p>
          <button className="btn-primary" onClick={onNew} style={{ marginTop: '1.5rem' }}>
            + New Assignment
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem' }}>
          {cases.map(c => (
            <div
              key={c.id}
              className="card"
              style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              onClick={() => onOpen(c.id)}
            >
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{c.id.slice(0, 8)}</div>
                <div style={{ fontWeight: 'bold', color: 'var(--text-strong)' }}>{formatCaseType(c.type)}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 2 }}>{c.statusMessage}</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem' }}>
                <StatusBadge status={c.status} />
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {new Date(c.updatedAt).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function formatCaseType(type) {
  return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
