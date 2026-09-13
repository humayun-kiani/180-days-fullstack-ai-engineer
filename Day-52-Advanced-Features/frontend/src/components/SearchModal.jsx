// frontend/src/components/SearchModal.jsx
import { useEffect, useRef, useState } from 'react'
import { Search, X, Clock, Tag } from 'lucide-react'
import { useSearch } from '../hooks/useSearch'
import clsx from 'clsx'

const PRIORITY_COLORS = {
  urgent: 'text-red-400', high: 'text-orange-400',
  medium: 'text-blue-400', low: 'text-gray-400'
}
const STATUS_LABELS = { pending: 'To Do', in_progress: 'In Progress', done: 'Done' }

export default function SearchModal({ onClose, onSelectTask }) {
  const inputRef = useRef(null)
  const { results, loading, query, search, clearSearch } = useSearch()
  const [selectedIdx, setSelectedIdx] = useState(0)

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Keyboard navigation within modal
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowDown') {
        setSelectedIdx((i) => Math.min(i + 1, results.length - 1))
        e.preventDefault()
      } else if (e.key === 'ArrowUp') {
        setSelectedIdx((i) => Math.max(i - 1, 0))
        e.preventDefault()
      } else if (e.key === 'Enter' && results[selectedIdx]) {
        onSelectTask?.(results[selectedIdx])
        onClose()
      } else if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [results, selectedIdx, onClose, onSelectTask])

  return (
    // Backdrop
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-start justify-center pt-[15vh]"
      onClick={onClose}
    >
      {/* Modal */}
      <div
        className="bg-gray-800 rounded-xl shadow-2xl border border-gray-700 w-full max-w-xl mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-700">
          <Search size={18} className="text-gray-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search tasks..."
            value={query}
            onChange={(e) => { search(e.target.value); setSelectedIdx(0) }}
            className="flex-1 bg-transparent text-white placeholder-gray-500 focus:outline-none text-sm"
          />
          {query && (
            <button onClick={() => { clearSearch(); inputRef.current?.focus() }}>
              <X size={16} className="text-gray-500 hover:text-white" />
            </button>
          )}
          <kbd className="text-xs text-gray-600 bg-gray-700 px-1.5 py-0.5 rounded">
            esc
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto">
          {loading && (
            <div className="py-8 text-center text-gray-500 text-sm">Searching...</div>
          )}

          {!loading && query && results.length === 0 && (
            <div className="py-8 text-center text-gray-500 text-sm">
              No tasks found for "{query}"
            </div>
          )}

          {!loading && !query && (
            <div className="py-8 text-center text-gray-600 text-sm">
              Type to search your tasks
            </div>
          )}

          {results.map((task, idx) => (
            <button
              key={task.id}
              onClick={() => { onSelectTask?.(task); onClose() }}
              className={clsx(
                'w-full text-left px-4 py-3 border-b border-gray-700/50 last:border-0',
                'flex items-start gap-3 transition-colors',
                idx === selectedIdx ? 'bg-gray-700' : 'hover:bg-gray-700/50'
              )}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={clsx('text-xs font-medium capitalize', PRIORITY_COLORS[task.priority])}>
                    {task.priority}
                  </span>
                  <span className="text-xs text-gray-500">
                    {STATUS_LABELS[task.status]}
                  </span>
                </div>
                <p className="text-sm text-white truncate">{task.title}</p>
                {task.description && (
                  <p className="text-xs text-gray-500 truncate mt-0.5">{task.description}</p>
                )}
              </div>
              <Clock size={12} className="text-gray-600 shrink-0 mt-1" />
            </button>
          ))}
        </div>

        {/* Footer with keyboard hints */}
        {results.length > 0 && (
          <div className="px-4 py-2 border-t border-gray-700 flex items-center gap-4 text-xs text-gray-600">
            <span>↑↓ navigate</span>
            <span>↵ open</span>
            <span>esc close</span>
          </div>
        )}
      </div>
    </div>
  )
}