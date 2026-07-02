/**
 * ConfidenceMeter — visual confidence bar + percentage label.
 * Shows green ≥ 0.7, gold 0.4–0.69, red < 0.4.
 */
export default function ConfidenceMeter({ confidence }) {
  const pct = Math.round((confidence ?? 0) * 100)
  const cls = pct >= 70 ? 'confidence-high' : pct >= 40 ? 'confidence-mid' : 'confidence-low'
  const label = pct >= 70 ? 'High confidence' : pct >= 40 ? 'Moderate confidence' : 'Low confidence — please verify carefully'
  return (
    <div style={{ marginBottom: '0.8rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 3 }}>
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="confidence-bar">
        <div className={`confidence-bar-fill ${cls}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
