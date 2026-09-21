// frontend/src/hooks/useOptimizedTasks.js
// Optimized task management with memoization

import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import client from '../api/client'

/**
 * Optimized task fetching with:
 * - Stable function references (useCallback)
 * - Memoized filtered/sorted results (useMemo)
 * - Deduped requests (ref-based guard)
 * - Optimistic updates
 */
export function useOptimizedTasks(filters = {}) {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const fetchingRef = useRef(false)   // prevent duplicate requests

  // Stable fetch function
  const fetchTasks = useCallback(async (params = {}) => {
    if (fetchingRef.current) return
    fetchingRef.current = true
    setLoading(true)
    try {
      const response = await client.get('/search', {
        params: { per_page: 100, ...filters, ...params }
      })
      setTasks(response.data.tasks)
      setTotal(response.data.total)
    } catch (err) {
      console.error('Failed to fetch tasks:', err)
    } finally {
      setLoading(false)
      fetchingRef.current = false
    }
  }, [JSON.stringify(filters)])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  // Memoized derived state — only recomputes when tasks change
  const tasksByStatus = useMemo(() => ({
    pending:     tasks.filter(t => t.status === 'pending'),
    in_progress: tasks.filter(t => t.status === 'in_progress'),
    done:        tasks.filter(t => t.status === 'done'),
  }), [tasks])

  const urgentCount = useMemo(
    () => tasks.filter(t => t.priority === 'urgent' && t.status !== 'done').length,
    [tasks]
  )

  const overdueCount = useMemo(
    () => tasks.filter(t => {
      if (!t.due_date || t.status === 'done') return false
      return new Date(t.due_date) < new Date()
    }).length,
    [tasks]
  )

  // Optimistic update — update UI before server confirms
  const optimisticUpdate = useCallback((taskId, changes) => {
    setTasks(prev => prev.map(t =>
      t.id === taskId ? { ...t, ...changes } : t
    ))
  }, [])

  // Optimistic delete
  const optimisticDelete = useCallback((taskId) => {
    setTasks(prev => prev.filter(t => t.id !== taskId))
    setTotal(prev => prev - 1)
  }, [])

  // Optimistic add
  const optimisticAdd = useCallback((task) => {
    setTasks(prev => [task, ...prev])
    setTotal(prev => prev + 1)
  }, [])

  return {
    tasks,
    loading,
    total,
    tasksByStatus,
    urgentCount,
    overdueCount,
    fetchTasks,
    optimisticUpdate,
    optimisticDelete,
    optimisticAdd,
  }
}


/**
 * Debounce a value — only update after delay.
 * Use for search inputs to avoid a request on every keystroke.
 */
export function useDebounce(value, delay = 250) {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debouncedValue
}