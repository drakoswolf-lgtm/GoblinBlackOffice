/**
 * App — root component wiring together the three top-level views:
 *   1. Dashboard  — list existing cases + "New Assignment" button
 *   2. GoblinPick — choose an operative
 *   3. CaseFlow   — the 5-stage workflow for a single case
 */

import { useState, useEffect } from 'react'
import { api } from './api/client'
import Dashboard from './pages/Dashboard'
import GoblinPick from './pages/GoblinPick'
import CaseFlow from './pages/CaseFlow'

export default function App() {
  const [view, setView] = useState('dashboard') // 'dashboard' | 'pick' | 'case'
  const [activeCaseId, setActiveCaseId] = useState(null)
  const [cases, setCases] = useState([])
  const [loadError, setLoadError] = useState(null)

  const refreshCases = async () => {
    try {
      const data = await api.listCases()
      setCases(data)
    } catch (e) {
      setLoadError(e.message)
    }
  }

  useEffect(() => { refreshCases() }, [])

  const openCase = (id) => { setActiveCaseId(id); setView('case') }
  const startNew = () => setView('pick')
  const goHome   = () => { refreshCases(); setView('dashboard') }

  const handleGoblinPicked = async (goblinId, caseType) => {
    try {
      const newCase = await api.createCase(caseType, goblinId)
      openCase(newCase.id)
    } catch (e) {
      alert(`Failed to create case: ${e.message}`)
    }
  }

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '1.5rem' }}>
      <Header onHome={goHome} onNew={startNew} showBack={view !== 'dashboard'} />

      {view === 'dashboard' && (
        <Dashboard
          cases={cases}
          error={loadError}
          onOpen={openCase}
          onNew={startNew}
          onRefresh={refreshCases}
        />
      )}
      {view === 'pick' && (
        <GoblinPick onPicked={handleGoblinPicked} onCancel={() => setView('dashboard')} />
      )}
      {view === 'case' && activeCaseId && (
        <CaseFlow caseId={activeCaseId} onDone={goHome} />
      )}
    </div>
  )
}

function Header({ onHome, onNew, showBack }) {
  return (
    <header style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button className="btn-secondary" onClick={onHome} style={{ fontSize: '1.3rem', padding: '0.2rem 0.8rem' }}>
          🧌 Goblin Black Office
        </button>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {showBack && (
            <button className="btn-secondary" onClick={onHome}>← Back</button>
          )}
          <button className="btn-primary" onClick={onNew}>+ New Assignment</button>
        </div>
      </div>
    </header>
  )
}
