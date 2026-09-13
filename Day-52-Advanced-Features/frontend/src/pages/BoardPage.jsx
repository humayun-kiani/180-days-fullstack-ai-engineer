// frontend/src/pages/BoardPage.jsx — Day 52 v2
import { useState, useEffect, useCallback } from 'react'
import {
  Filter, RefreshCw, Download, BarChart3, Search,
  Keyboard, SortAsc, SortDesc, ChevronDown
} from 'lucide-react'
import { listTasks, updateTask, deleteTask } from '../api/tasks'
import TaskCard from '../components/TaskCard'
import TaskForm from '../components/TaskForm'
import AIPanel from '../components/AIPanel'
import NavBar from '../components/NavBar'
import SearchModal from '../components/SearchModal'
import KeyboardHelp from '../components/KeyboardHelp'
import StatsPanel from '../components/StatsPanel'
import BulkActions from '../components/BulkActions'
import Pagination from '../components/Pagination'
import { useWebSocket } from '../hooks/useWebSocket'
import { useKeyboardShortcuts } from '../hooks/useKeyboard'
import client from '../api/client'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const STATUSES = ['pending', 'in_progress', 'done']
const STATUS_LABELS = { pending: 'To Do', in_progress: 'In Progress', done: 'Done' }
const STATUS_COLORS = {
  pending: 'border-gray-700',
  in_progress: 'border-blue-700',
  done: 'border-green-700'
}
const SORT_OPTIONS = [
  { value: 'created_at', label: 'Date Created' },
  { value: 'updated_at', label: 'Last Updated' },
  { value: 'priority', label: 'Priority' },
  { value: 'due_date', label: 'Due Date' },
  { value: 'title', label: 'Title' },
]

export default function BoardPage() {
  // State
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(0)
  const perPage = 20

  // Filters
  const [filter, setFilter] = useState({ priority: '', status: '' })
  const [sortBy, setSortBy] = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')

  // UI state
  const [showSearch, setShowSearch] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [showStats, setShowStats] = useState(false)
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [newTaskOpen, setNewTaskOpen] = useState(false)

  // Fetch tasks (using search endpoint for sorting + filtering)
  const fetchTasks = useCallback(async (p = page) => {
    setLoading(true)
    try {
      const params = {
        page: p,
        per_page: perPage,
        sort_by: sortBy,
        sort_dir: sortDir,
      }
      if (filter.priority) params.priority = filter.priority
      if (filter.status) params.status = filter.status

      const res = await client.get('/search', { params })
      setTasks(res.data.tasks)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch (err) {
      toast.error('Failed to load tasks')
    } finally {
      setLoading(false)
    }
  }, [filter, sortBy, sortDir, page, perPage])

  useEffect(() => {
    fetchTasks(1)
    setPage(1)
    setSelectedIds(new Set())
  }, [filter, sortBy, sortDir])

  useEffect(() => { fetchTasks(page) }, [page])

  // WebSocket real-time updates
  useWebSocket(useCallback((msg) => {
    if (['task_created', 'task_updated', 'task_deleted'].includes(msg.type)) {
      fetchTasks(page)
    }
  }, [fetchTasks, page]))

  // Keyboard shortcuts
  useKeyboardShortcuts([
    { key: 'k', callback: () => setShowSearch(true), options: { ctrl: true } },
    { key: 'n', callback: () => setNewTaskOpen(true) },
    { key: '?', callback: () => setShowHelp(true) },
    { key: 'r', callback: () => fetchTasks(page) },
    { key: 's', callback: () => setShowStats((v) => !v) },
    { key: 'e', callback: handleExportCSV },
    { key: 'Escape', callback: () => {
      setShowSearch(false); setShowHelp(false)
      setSelectedIds(new Set())
    }},
  ])

  // Task operations
  const handleCreated = (task) => { fetchTasks(1); setPage(1) }
  const handleUpdate = (updated) => {
    setTasks((prev) => prev.map((t) => t.id === updated.id ? updated : t))
  }
  const handleDelete = (id) => {
    setTasks((prev) => prev.filter((t) => t.id !== id))
    setSelectedIds((prev) => { const next = new Set(prev); next.delete(id); return next })
    setTotal((t) => t - 1)
  }

  // Selection
  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  // Bulk operations
  const handleBulkStatusChange = async (status) => {
    const ids = [...selectedIds]
    // Optimistic update
    setTasks((prev) => prev.map((t) => selectedIds.has(t.id) ? { ...t, status } : t))

    try {
      await Promise.all(ids.map((id) => updateTask(id, { status })))
      setSelectedIds(new Set())
      toast.success(`${ids.length} tasks updated`)
    } catch (err) {
      fetchTasks(page)  // rollback on error
      toast.error('Bulk update failed')
    }
  }

  const handleBulkDelete = async () => {
    if (!confirm(`Delete ${selectedIds.size} tasks?`)) return
    const ids = [...selectedIds]
    setTasks((prev) => prev.filter((t) => !selectedIds.has(t.id)))
    setSelectedIds(new Set())

    try {
      await Promise.all(ids.map((id) => deleteTask(id)))
      toast.success(`${ids.length} tasks deleted`)
    } catch (err) {
      fetchTasks(page)
      toast.error('Bulk delete failed')
    }
  }

  // Export
  function handleExportCSV() {
    const token = localStorage.getItem('access_token')
    const params = new URLSearchParams()
    if (filter.priority) params.set('priority', filter.priority)
    if (filter.status) params.set('status', filter.status)
    window.open(`/api/tasks/export/csv?${params.toString()}`, '_blank')
  }

  function handleExportJSON() {
    const params = new URLSearchParams()
    if (filter.priority) params.set('priority', filter.priority)
    if (filter.status) params.set('status', filter.status)
    window.open(`/api/tasks/export/json?${params.toString()}`, '_blank')
  }

  const tasksByStatus = (status) => tasks.filter((t) => t.status === status)

  const toggleSort = (field) => {
    if (sortBy === field) {
      setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortDir('desc')
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <NavBar />

      {/* Modals */}
      {showSearch && (
        <SearchModal
          onClose={() => setShowSearch(false)}
          onSelectTask={(t) => toast(`Task: ${t.title}`, { icon: '📋' })}
        />
      )}
      {showHelp && <KeyboardHelp onClose={() => setShowHelp(false)} />}

      {/* Bulk actions bar */}
      <BulkActions
        selectedIds={selectedIds}
        totalCount={tasks.length}
        onSelectAll={() => setSelectedIds(new Set(tasks.map((t) => t.id)))}
        onClearSelection={() => setSelectedIds(new Set())}
        onBulkDelete={handleBulkDelete}
        onBulkStatusChange={handleBulkStatusChange}
      />

      <div className="max-w-7xl mx-auto px-4 py-5">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-3 mb-5">
          <h1 className="text-lg font-bold">Task Board</h1>

          {/* Search button */}
          <button
            onClick={() => setShowSearch(true)}
            className="flex items-center gap-1.5 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
          >
            <Search size={14} />
            Search
            <kbd className="text-xs bg-gray-700 px-1 rounded ml-1">⌘K</kbd>
          </button>

          {/* Sort */}
          <div className="flex items-center gap-1">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-sm text-gray-300 focus:outline-none"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <button
              onClick={() => setSortDir((d) => d === 'asc' ? 'desc' : 'asc')}
              className="p-1.5 bg-gray-800 border border-gray-700 rounded-lg text-gray-300 hover:bg-gray-700"
            >
              {sortDir === 'asc' ? <SortAsc size={14} /> : <SortDesc size={14} />}
            </button>
          </div>

          {/* Priority filter */}
          <select
            value={filter.priority}
            onChange={(e) => setFilter((f) => ({ ...f, priority: e.target.value }))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none"
          >
            <option value="">All priorities</option>
            {['urgent', 'high', 'medium', 'low'].map((p) => (
              <option key={p} value={p} className="capitalize">{p}</option>
            ))}
          </select>

          {/* Right actions */}
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => setShowStats((v) => !v)}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border transition-colors',
                showStats
                  ? 'bg-blue-700 border-blue-600 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700'
              )}
            >
              <BarChart3 size={14} />
              Stats
            </button>

            <div className="relative group">
              <button className="flex items-center gap-1.5 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors">
                <Download size={14} />
                Export
                <ChevronDown size={12} />
              </button>
              <div className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-700 rounded-lg overflow-hidden hidden group-hover:block z-10 min-w-[120px]">
                <button
                  onClick={handleExportCSV}
                  className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700"
                >
                  CSV
                </button>
                <button
                  onClick={handleExportJSON}
                  className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700"
                >
                  JSON
                </button>
              </div>
            </div>

            <button
              onClick={() => fetchTasks(page)}
              className="p-1.5 text-gray-400 hover:text-white transition-colors"
              title="Refresh (R)"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>

            <button
              onClick={() => setShowHelp(true)}
              className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors"
              title="Keyboard shortcuts (?)"
            >
              <Keyboard size={16} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
          {/* Left sidebar */}
          <div className="space-y-4">
            <TaskForm onCreated={handleCreated} />
            <AIPanel />
            <StatsPanel visible={showStats} />
          </div>

          {/* Kanban board */}
          <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-4">
            {STATUSES.map((status) => {
              const col = tasksByStatus(status)
              return (
                <div key={status} className={`bg-gray-900 rounded-xl p-4 border ${STATUS_COLORS[status]}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-sm text-gray-300">
                      {STATUS_LABELS[status]}
                    </h3>
                    <span className="text-xs bg-gray-700 text-gray-400 rounded-full px-2 py-0.5">
                      {col.length}
                    </span>
                  </div>

                  {loading ? (
                    <div className="text-center py-8 text-gray-600 text-sm">Loading...</div>
                  ) : col.length === 0 ? (
                    <div className="text-center py-8 text-gray-700 text-sm">No tasks</div>
                  ) : (
                    col.map((task) => (
                      <div key={task.id} className="relative group">
                        {/* Select checkbox */}
                        <div
                          className={clsx(
                            'absolute top-3 left-3 z-10 transition-opacity cursor-pointer',
                            selectedIds.has(task.id) ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                          )}
                          onClick={(e) => { e.stopPropagation(); toggleSelect(task.id) }}
                        >
                          <div className={clsx(
                            'w-4 h-4 rounded border flex items-center justify-center',
                            selectedIds.has(task.id)
                              ? 'bg-blue-600 border-blue-500'
                              : 'border-gray-600 bg-gray-800'
                          )}>
                            {selectedIds.has(task.id) && (
                              <svg viewBox="0 0 12 12" className="w-2.5 h-2.5 text-white">
                                <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
                              </svg>
                            )}
                          </div>
                        </div>
                        <TaskCard
                          task={task}
                          onUpdate={handleUpdate}
                          onDelete={handleDelete}
                        />
                      </div>
                    ))
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Pagination */}
        {pages > 1 && (
          <div className="mt-6">
            <Pagination
              page={page}
              pages={pages}
              total={total}
              perPage={perPage}
              onPageChange={(p) => { setPage(p); setSelectedIds(new Set()) }}
            />
          </div>
        )}

        {/* Keyboard hint */}
        <div className="fixed bottom-4 right-4 text-xs text-gray-700">
          <button
            onClick={() => setShowHelp(true)}
            className="flex items-center gap-1 hover:text-gray-500 transition-colors"
          >
            <Keyboard size={12} />
            ? for shortcuts
          </button>
        </div>
      </div>
    </div>
  )
}