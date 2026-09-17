// frontend/src/components/AccessibleModal.jsx
import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { useFocusTrap } from '../hooks/useA11y'

/**
 * Accessible modal dialog.
 *
 * - role="dialog" + aria-modal="true"
 * - Focus trapped inside
 * - Closes on Escape
 * - Returns focus to trigger on close
 * - Labels via aria-labelledby
 */
export default function AccessibleModal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md'   // 'sm' | 'md' | 'lg'
}) {
  const containerRef = useFocusTrap(isOpen)
  const previousFocusRef = useRef(null)

  // Save focus and close on Escape
  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement
    } else {
      previousFocusRef.current?.focus()
    }

    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      window.addEventListener('keydown', handleEsc)
      // Prevent body scroll on mobile
      document.body.style.overflow = 'hidden'
    }
    return () => {
      window.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = ''
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-2xl'
  }

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
      role="presentation"
      onClick={onClose}
    >
      {/* Dimmed overlay */}
      <div className="fixed inset-0 bg-black/60" aria-hidden="true" />

      {/* Dialog */}
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={`
          relative z-10 bg-gray-800 border border-gray-700 shadow-2xl
          w-full ${sizeClasses[size]} mx-4
          rounded-t-2xl sm:rounded-2xl
          max-h-[90vh] overflow-y-auto
        `}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-700">
          <h2 id="modal-title" className="text-white font-semibold text-lg">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="
              min-w-[44px] min-h-[44px] flex items-center justify-center
              text-gray-400 hover:text-white hover:bg-gray-700
              rounded-lg transition-colors
              focus:outline-none focus:ring-2 focus:ring-blue-500
            "
            aria-label="Close dialog"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5">
          {children}
        </div>
      </div>
    </div>
  )
}