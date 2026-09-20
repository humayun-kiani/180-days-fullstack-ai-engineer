// frontend/src/__tests__/hooks/useSwipe.test.js
import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSwipe } from '../../hooks/useSwipe'

function createTouchEvent(clientX, clientY = 0) {
  return { targetTouches: [{ clientX, clientY }] }
}

describe('useSwipe', () => {
  it('calls onSwipeLeft when swiping left past threshold', () => {
    const onLeft = vi.fn()
    const onRight = vi.fn()
    const { result } = renderHook(() => useSwipe(onLeft, onRight, 50))

    act(() => result.current.onTouchStart(createTouchEvent(200)))
    act(() => result.current.onTouchMove(createTouchEvent(140)))  // dx = -60 (left)
    act(() => result.current.onTouchEnd())

    expect(onLeft).toHaveBeenCalledOnce()
    expect(onRight).not.toHaveBeenCalled()
  })

  it('calls onSwipeRight when swiping right past threshold', () => {
    const onLeft = vi.fn()
    const onRight = vi.fn()
    const { result } = renderHook(() => useSwipe(onLeft, onRight, 50))

    act(() => result.current.onTouchStart(createTouchEvent(100)))
    act(() => result.current.onTouchMove(createTouchEvent(170)))  // dx = +70 (right)
    act(() => result.current.onTouchEnd())

    expect(onRight).toHaveBeenCalledOnce()
    expect(onLeft).not.toHaveBeenCalled()
  })

  it('does NOT swipe if distance below threshold', () => {
    const onLeft = vi.fn()
    const onRight = vi.fn()
    const { result } = renderHook(() => useSwipe(onLeft, onRight, 50))

    act(() => result.current.onTouchStart(createTouchEvent(100)))
    act(() => result.current.onTouchMove(createTouchEvent(130)))  // dx = +30 (below 50)
    act(() => result.current.onTouchEnd())

    expect(onLeft).not.toHaveBeenCalled()
    expect(onRight).not.toHaveBeenCalled()
  })

  it('cancels swipe if vertical movement too large', () => {
    const onLeft = vi.fn()
    const { result } = renderHook(() => useSwipe(onLeft, vi.fn(), 50, 80))

    act(() => result.current.onTouchStart(createTouchEvent(200, 0)))
    act(() => result.current.onTouchMove(createTouchEvent(100, 100)))  // 100px vertical
    act(() => result.current.onTouchEnd())

    expect(onLeft).not.toHaveBeenCalled()
  })

  it('uses custom threshold', () => {
    const onLeft = vi.fn()
    const { result } = renderHook(() => useSwipe(onLeft, vi.fn(), 100))

    act(() => result.current.onTouchStart(createTouchEvent(200)))
    act(() => result.current.onTouchMove(createTouchEvent(140)))  // only 60px
    act(() => result.current.onTouchEnd())

    // 60 < 100 threshold — should NOT fire
    expect(onLeft).not.toHaveBeenCalled()
  })

  it('does nothing if touchEnd without touchMove', () => {
    const onLeft = vi.fn()
    const { result } = renderHook(() => useSwipe(onLeft, vi.fn()))

    act(() => result.current.onTouchStart(createTouchEvent(200)))
    act(() => result.current.onTouchEnd())

    expect(onLeft).not.toHaveBeenCalled()
  })
})