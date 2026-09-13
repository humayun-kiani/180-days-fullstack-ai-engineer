// frontend/src/components/BulkActions.jsx
import { Trash2, CheckSquare, Square, X } from 'lucide-react'
import clsx from 'clsx'

export default function BulkActions({
  selectedIds,
  totalCount,
  onSelectAll,
  onClearSelection,
  onBulkDelete,
  onBulkStatusChange
}) {
  if (selectedIds.size === 0) return null

  const count = selectedIds.size

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40">
      <div className="bg-gray-800 border border-gray-600 rounded-xl px-5 py-3 shadow-2xl flex items-center gap-4">
        {/* Selection info */}
        <div className="flex items-center gap-2">
          <CheckSquare size={16} className="text-blue-400" />
          <span className="text-white text-sm font-medium">{count} selected</span>
        </div>

        <div className="w-px h-5 bg-gray-600" />

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onBulkStatusChange('done')}
            className="text-xs bg-green-700 hover:bg-green-600 text-white px-3 py-1.5 rounded-lg transition-colors"
          >
            Mark Done
          </button>
          <button
            onClick={() => onBulkStatusChange('in_progress')}
            className="text-xs bg-blue-700 hover:bg-blue-600 text-white px-3 py-1.5 rounded-lg transition-colors"
          >
            In Progress
          </button>
          <button
            onClick={onBulkDelete}
            className="text-xs bg-red-800 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1"
          >
            <Trash2 size={12} />
            Delete
          </button>
        </div>

        <div className="w-px h-5 bg-gray-600" />

        {/* Clear selection */}
        <button
          onClick={onClearSelection}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  )
}