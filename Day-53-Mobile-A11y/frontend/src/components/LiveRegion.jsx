// frontend/src/components/LiveRegion.jsx
/**
 * Invisible container that announces content to screen readers.
 *
 * Use for: task created/deleted, status changes, AI results.
 */
export default function LiveRegion({ message, mode = 'polite' }) {
  return (
    <div
      aria-live={mode}
      aria-atomic="true"
      className="sr-only"
      role={mode === 'assertive' ? 'alert' : 'status'}
    >
      {message}
    </div>
  )
}

/**
 * Error announcement — interrupts screen reader immediately.
 */
export function ErrorAnnouncement({ message }) {
  return (
    <div
      aria-live="assertive"
      aria-atomic="true"
      role="alert"
      className="sr-only"
    >
      {message}
    </div>
  )
}