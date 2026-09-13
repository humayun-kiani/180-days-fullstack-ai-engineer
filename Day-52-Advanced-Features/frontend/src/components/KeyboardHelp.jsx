// frontend/src/components/KeyboardHelp.jsx
import { X, Keyboard } from 'lucide-react'

const SHORTCUTS = [
  { keys: ['N'], description: 'New task' },
  { keys: ['Ctrl', 'K'], description: 'Search tasks' },
  { keys: ['?'], description: 'Show this help' },
  { keys: ['Esc'], description: 'Close modals' },
  { keys: ['R'], description: 'Refresh tasks' },
  { keys: ['E'], description: 'Export CSV' },
  { keys: ['S'], description: 'Toggle stats' },
]

export default function KeyboardHelp({ onClose }) {
  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 rounded-xl border border-gray-700 shadow-2xl w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <Keyboard size={18} className="text-blue-400" />
            <h3 className="text-white font-semibold">Keyboard Shortcuts</h3>
          </div>
          <button onClick={onClose}>
            <X size={18} className="text-gray-400 hover:text-white" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-3">
          {SHORTCUTS.map(({ keys, description }) => (
            <div key={description} className="flex items-center justify-between">
              <span className="text-sm text-gray-300">{description}</span>
              <div className="flex items-center gap-1">
                {keys.map((k) => (
                  <kbd
                    key={k}
                    className="bg-gray-700 text-gray-300 px-2 py-0.5 rounded text-xs font-mono"
                  >
                    {k}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="px-5 py-3 border-t border-gray-700">
          <p className="text-xs text-gray-600 text-center">
            Press <kbd className="bg-gray-700 px-1 rounded">Esc</kbd> to close
          </p>
        </div>
      </div>
    </div>
  )
}