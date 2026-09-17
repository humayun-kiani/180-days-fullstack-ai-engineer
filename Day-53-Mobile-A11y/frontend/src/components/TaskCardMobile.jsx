// frontend/src/components/TaskCardMobile.jsx
import { useState, useCallback } from 'react'
import { Check, Trash2, ChevronRight, Sparkles } from 'lucide-react'
import clsx from 'clsx'
import { useSwipe } from '../hooks/useSwipe'
import { usePrefersReducedMotion } from '../hooks/useA11y'

const PRIORITY_CONFIG = {
  urgent: { bg: 'bg-red-900/40', border: 'border-red-700', text: 'text-red-300', dot: 'bg-red-500' },
  high:   { bg: 'bg-orange-900/40', border: 'border-orange-700', text: 'text-orange-300', dot: 'bg-orange-500' },
  medium: { bg: 'bg-blue-900/30', border: 'border-blue-800', text: 'text-blue-300', dot: 'bg-blue-500' },
  low:    { bg: 'bg-gray-800', border: 'border-gray-700', text: 'text-gray-400', dot: 'bg-gray-500' },
}

const STATUS_LABELS = {
  pending: 'To Do',
  in_progress: 'In Progress',
  done: 'Done'
}

/**
 * Mobile-optimized task card with swipe gestures.
 *
 * Swipe left: delete (shows red background)
 * Swipe right: mark done (shows green background)
 * Large tap targets throughout.
 */
export default function TaskCardMobile({
  task,
  onDelete,
  onStatusChange,
  onExpand
}) {
  const [dismissed, setDismissed] = useState(false)
  const [swipeOffset, setSwipeOffset] = useState(0)
  const prefersReduced = usePrefersReducedMotion()

  const handleSwipeLeft = useCallback(() => {
    if (prefersReduced) {
      onDelete?.(task.id)
      return
    }
    setDismissed('left')
    setTimeout(() => onDelete?.(task.id), 250)
  }, [task.id, onDelete, prefersReduced])

  const handleSwipeRight = useCallback(() => {
    if (task.status === 'done') return
    if (prefersReduced) {
      onStatusChange?.(task.id, 'done')
      return
    }
    setDismissed('right')
    setTimeout(() => onStatusChange?.(task.id, 'done'), 250)
  }, [task.id, task.status, onStatusChange, prefersReduced])

  const swipeHandlers = useSwipe(handleSwipeLeft, handleSwipeRight, 60)
  const config = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.medium

  const isOverdue = task.due_date &&
    new Date(task.due_date) < new Date() &&
    task.status !== 'done'

  if (dismissed) return null

  return (
    <div className="relative overflow-hidden rounded-xl mb-3">
      {/* Swipe hint backgrounds */}
      <div className="absolute inset-0 flex items-center justify-between px-4" aria-hidden="true">
        <div className="bg-green-600/80 rounded-lg p-2">
          <Check size={20} className="text-white" />
        </div>
        <div className="bg-red-600/80 rounded-lg p-2">
          <Trash2 size={20} className="text-white" />
        </div>
      </div>

      {/* Card */}
      <article
        {...swipeHandlers}
        className={clsx(
          'relative p-4 border rounded-xl',
          'transition-transform will-change-transform',
          !prefersReduced && 'duration-[50ms]',
          config.bg, config.border,
          dismissed === 'left' && '-translate-x-full opacity-0 duration-300',
          dismissed === 'right' && 'translate-x-full opacity-0 duration-300'
        )}
        aria-label={`Task: ${task.title}. Priority: ${task.priority}. Status: ${STATUS_LABELS[task.status]}.${isOverdue ? ' Overdue.' : ''}`}
      >
        {/* Priority dot + status */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div
              className={clsx('w-2 h-2 rounded-full', config.dot)}
              aria-hidden="true"
            />
            <span className={clsx('text-xs font-medium capitalize', config.text)}>
              {task.priority}
            </span>
            {isOverdue && (
              <span className="text-xs text-red-400 font-medium" role="img" aria-label="Overdue">
                ⚠ Overdue
              </span>
            )}
          </div>
          <span className="text-xs text-gray-500">
            {STATUS_LABELS[task.status]}
          </span>
        </div>

        {/* Title */}
        <h3 className="text-white font-medium text-sm leading-snug mb-1">
          {task.title}
        </h3>

        {/* Description preview */}
        {task.description && (
          <p className="text-xs text-gray-400 line-clamp-2 mb-2">
            {task.description}
          </p>
        )}

        {/* AI summary badge */}
        {task.ai_summary && (
          <div className="flex items-center gap-1 mb-2">
            <Sparkles size={10} className="text-purple-400" aria-hidden="true" />
            <span className="text-xs text-purple-400 line-clamp-1">{task.ai_summary}</span>
          </div>
        )}

        {/* Actions row */}
        <div className="flex items-center gap-2 mt-3">
          {task.status !== 'done' && (
            <button
              onClick={() => onStatusChange?.(task.id, 'done')}
              className="
                flex items-center gap-1
                min-h-[40px] px-3
                bg-green-800/50 hover:bg-green-700/60
                text-green-300 text-xs rounded-lg
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-green-500
              "
              aria-label={`Mark task "${task.title}" as done`}
            >
              <Check size={14} aria-hidden="true" />
              Done
            </button>
          )}

          <button
            onClick={() => onExpand?.(task)}
            className="
              flex items-center gap-1 ml-auto
              min-h-[40px] px-3
              text-gray-400 hover:text-white text-xs
              transition-colors
              focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg
            "
            aria-label={`View details for task "${task.title}"`}
            aria-haspopup="dialog"
          >
            Details
            <ChevronRight size={14} aria-hidden="true" />
          </button>
        </div>
      </article>
    </div>
  )
}