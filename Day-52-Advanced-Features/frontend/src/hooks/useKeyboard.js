// frontend/src/hooks/useKeyboard.js
import { useEffect, useCallback } from 'react'

/**
 * Register a global keyboard shortcut.
 *
 * @param {string} key - The key to listen for (e.g. 'k', 'Escape')
 * @param {Function} callback - Called when shortcut fires
 * @param {Object} options - { ctrl, meta, shift, ignoreInput }
 */
export function useKeyboardShortcut(key, callback, options = {}) {
  const {
    ctrl = false,
    meta = false,
    shift = false,
    ignoreInput = true
  } = options

  const stableCallback = useCallback(callback, [callback])

  useEffect(() => {
    const handler = (e) => {
      // Skip if typing in an input/textarea (unless explicitly allowed)
      if (ignoreInput && (
        e.target.tagName === 'INPUT' ||
        e.target.tagName === 'TEXTAREA' ||
        e.target.isContentEditable
      )) return

      if (ctrl && !e.ctrlKey && !e.metaKey) return
      if (meta && !e.metaKey) return
      if (shift && !e.shiftKey) return

      if (e.key.toLowerCase() === key.toLowerCase()) {
        e.preventDefault()
        stableCallback()
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [key, ctrl, meta, shift, ignoreInput, stableCallback])
}

/**
 * Register multiple keyboard shortcuts at once.
 *
 * @param {Array} shortcuts - [{key, callback, options}]
 */
export function useKeyboardShortcuts(shortcuts) {
  useEffect(() => {
    const handler = (e) => {
      const isInput = e.target.tagName === 'INPUT' ||
                      e.target.tagName === 'TEXTAREA' ||
                      e.target.isContentEditable

      for (const { key, callback, options = {} } of shortcuts) {
        const { ctrl = false, ignoreInput = true } = options
        if (ignoreInput && isInput) continue
        if (ctrl && !e.ctrlKey && !e.metaKey) continue
        if (e.key.toLowerCase() === key.toLowerCase()) {
          e.preventDefault()
          callback()
          break
        }
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [shortcuts])
}