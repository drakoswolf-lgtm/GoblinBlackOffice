/** StatusBadge — coloured pill matching the CSS badge classes. */
export default function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>
}
