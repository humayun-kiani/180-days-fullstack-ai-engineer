// frontend/src/hooks/useA11y.js
import { useEffect, useRef, useCallback } from 'react'

/**
 * Trap focus within a container (for modals/dialogs).
 * Tab cycles through focusable elements within container.
 */
export function useFocusTrap(isActive) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!isActive || !containerRef.current) return

    const container = containerRef.current
    const focusable = container.querySelectorAll(
      'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), ' +
      'select:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'
    )
    const firstFocusable = focusable[0]
    const lastFocusable = focusable[focusable.length - 1]

    // Focus first element on mount
    firstFocusable?.focus()

    const handleTab = (e) => {
      if (e.key !== 'Tab') return

      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          lastFocusable?.focus()
          e.preventDefault()
        }
      } else {
        if (document.activeElement === lastFocusable) {
          firstFocusable?.focus()
          e.preventDefault()
        }
      }
    }

    container.addEventListener('keydown', handleTab)
    return () => container.removeEventListener('keydown', handleTab)
  }, [isActive])

  return containerRef
}


/**
 * Return focus to a trigger element when a modal closes.
 */
export function useFocusReturn(isOpen) {
  const triggerRef = useRef(null)

  useEffect(() => {
    if (isOpen) {
      triggerRef.current = document.activeElement
    } else {
      triggerRef.current?.focus()
    }
  }, [isOpen])
}


/**
 * Announce a message to screen readers via aria-live.
 */
export function useAnnounce() {
  const [message, setMessage] = React.useState('')

  const announce = useCallback((text, delay = 100) => {
    // Clear first so same message re-announces
    setMessage('')
    setTimeout(() => setMessage(text), delay)
  }, [])

  return { message, announce }
}


/**
 * Detect if user prefers reduced motion.
 */
export function usePrefersReducedMotion() {
  const [prefersReduced, setPrefersReduced] = React.useState(false)

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReduced(mq.matches)
    const handler = (e) => setPrefersReduced(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  return prefersReduced
}