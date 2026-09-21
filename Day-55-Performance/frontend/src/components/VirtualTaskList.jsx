// frontend/src/components/VirtualTaskList.jsx
// Virtual scrolling for large task lists (100+ tasks)

import { useRef, useMemo } from 'react'
import React from 'react'

const ITEM_HEIGHT = 88  // px — estimated height per task card

/**
 * Simple virtual scrolling implementation.
 * Renders only tasks visible in the viewport + overscan buffer.
 *
 * For production: use @tanstack/react-virtual for better support.
 * This is a simplified educational version.
 */
export default function VirtualTaskList({ tasks, renderItem, height = 600 }) {
  const containerRef = useRef(null)
  const [scrollTop, setScrollTop] = React.useState(0)

  const totalHeight = tasks.length * ITEM_HEIGHT
  const overscan = 3

  // Calculate which items are visible
  const { startIndex, endIndex, offsetTop } = useMemo(() => {
    const start = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - overscan)
    const visible = Math.ceil(height / ITEM_HEIGHT)
    const end = Math.min(tasks.length - 1, start + visible + overscan * 2)
    return {
      startIndex: start,
      endIndex: end,
      offsetTop: start * ITEM_HEIGHT
    }
  }, [scrollTop, tasks.length, height])

  const visibleTasks = tasks.slice(startIndex, endIndex + 1)

  return (
    <div
      ref={containerRef}
      style={{ height, overflowY: 'auto' }}
      onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
      role="list"
      aria-label={`${tasks.length} tasks`}
    >
      {/* Full height spacer */}
      <div style={{ height: totalHeight, position: 'relative' }}>
        {/* Only render visible items */}
        <div style={{ position: 'absolute', top: offsetTop, width: '100%' }}>
          {visibleTasks.map((task, i) => (
            <div
              key={task.id}
              style={{ height: ITEM_HEIGHT }}
              role="listitem"
            >
              {renderItem(task, startIndex + i)}
            </div>
          ))}
        </div>
      </div>

      {/* Performance info (dev only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-20 right-4 text-xs text-gray-600 bg-gray-900 px-2 py-1 rounded">
          Rendering {visibleTasks.length}/{tasks.length} items
        </div>
      )}
    </div>
  )
}


/**
 * React.memo wrapper for task cards used in virtual list.
 * Prevents re-renders when other tasks change.
 */
export const MemoizedTaskCard = React.memo(function MemoizedTaskCard({
  task,
  onUpdate,
  onDelete
}) {
  // Only re-renders if task object or callbacks change
  return null // Replace with actual TaskCard import
}, (prevProps, nextProps) => {
  // Custom comparison: only re-render if task data changed
  return (
    prevProps.task.id === nextProps.task.id &&
    prevProps.task.status === nextProps.task.status &&
    prevProps.task.priority === nextProps.task.priority &&
    prevProps.task.title === nextProps.task.title &&
    prevProps.task.updated_at === nextProps.task.updated_at
  )
})