// frontend/src/hooks/useSwipe.js
import { useRef, useCallback } from 'react'

/**
 * Detect horizontal swipe gestures on touch devices.
 *
 * @param {Function} onSwipeLeft - Called when swiped left
 * @param {Function} onSwipeRight - Called when swiped right
 * @param {number} threshold - Minimum px distance for swipe (default 50)
 * @param {number} maxVertical - Max vertical movement before cancelling (default 100)
 */
export function useSwipe(
  onSwipeLeft,
  onSwipeRight,
  threshold = 50,
  maxVertical = 100
) {
  const touchStartX = useRef(null)
  const touchStartY = useRef(null)
  const touchEndX = useRef(null)
  const touchEndY = useRef(null)
  const swiping = useRef(false)

  const onTouchStart = useCallback((e) => {
    touchStartX.current = e.targetTouches[0].clientX
    touchStartY.current = e.targetTouches[0].clientY
    touchEndX.current = null
    touchEndY.current = null
    swiping.current = true
  }, [])

  const onTouchMove = useCallback((e) => {
    if (!swiping.current) return
    touchEndX.current = e.targetTouches[0].clientX
    touchEndY.current = e.targetTouches[0].clientY

    // Cancel if user is scrolling vertically
    const verticalDistance = Math.abs(
      (touchEndY.current || 0) - (touchStartY.current || 0)
    )
    if (verticalDistance > maxVertical) {
      swiping.current = false
    }
  }, [maxVertical])

  const onTouchEnd = useCallback(() => {
    if (!swiping.current || touchEndX.current === null) return
    swiping.current = false

    const horizontalDistance = touchStartX.current - touchEndX.current
    const verticalDistance = Math.abs(
      touchEndY.current - touchStartY.current
    )

    // Require predominantly horizontal movement
    if (verticalDistance > Math.abs(horizontalDistance) * 0.7) return

    if (horizontalDistance > threshold) onSwipeLeft?.()
    if (horizontalDistance < -threshold) onSwipeRight?.()
  }, [threshold, onSwipeLeft, onSwipeRight])

  return { onTouchStart, onTouchMove, onTouchEnd }
}


/**
 * Get current swipe offset for animated feedback.
 */
export function useSwipeWithFeedback(onSwipeLeft, onSwipeRight, threshold = 50) {
  const touchStartX = useRef(null)
  const [offset, setOffset] = React.useState(0)

  const onTouchStart = useCallback((e) => {
    touchStartX.current = e.targetTouches[0].clientX
    setOffset(0)
  }, [])

  const onTouchMove = useCallback((e) => {
    if (touchStartX.current === null) return
    const dx = e.targetTouches[0].clientX - touchStartX.current
    setOffset(dx)
  }, [])

  const onTouchEnd = useCallback(() => {
    if (offset > threshold) onSwipeRight?.()
    else if (offset < -threshold) onSwipeLeft?.()
    setOffset(0)
    touchStartX.current = null
  }, [offset, threshold, onSwipeLeft, onSwipeRight])

  return { onTouchStart, onTouchMove, onTouchEnd, offset }
}