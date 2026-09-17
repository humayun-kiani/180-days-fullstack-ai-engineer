// frontend/src/pages/BoardPageMobile.jsx
import { useState, useEffect, useCallback } from 'react'
import { Brain } from 'lucide-react'
import { listTasks, createTask, updateTask, deleteTask } from '../api/tasks'
import { analyzeTask, expandTask } from '../api/ai'
import TaskCardMobile from '../components/TaskCardMobile'
import TaskFormMobile from '../components/TaskFormMobile'
import MobileNav from '../components/MobileNav'
import AccessibleModal from '../components/AccessibleModal'
import SearchModal from '../components/SearchModal'
import SkipLink from '../components/SkipLink'
import LiveRegion from '../components/LiveRegion'
import { useWebSocket } from '../hooks/useWebSocket'
import { useKeyboardShortcut } from '../hooks/useKeyboard'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import useAuthStore from '../store/authStore'

const VIEWS = ['pending', 'in_progress', 'done']
const VIEW_LABELS = { pending: 'To Do', in_progress: 'In Progress', done: 'Done' }

export default function BoardPageMobile() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState('pending')
  const [modals, setModals] = useState({ newTask: false, search: false, detail: null })
  const [announcement, setAnnouncement] = useState('')
  const { user } = useAuthStore()

  const announce = useCallback((msg) => {
    setAnnouncement('')
    setTimeout(() => setAnnouncement(msg), 50)
  }, [])

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listTasks({ per_page: 100 })
      setTasks(data.tasks)
    } catch (err) {
      toast.error('Could not load tasks')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchTasks() }, [fetchTasks])

  useWebSocket(useCallback((msg) => {
    if (['task_created', 'task_updated', 'task_deleted'].includes(msg.type)) {
      fetchTasks()
    }
  }, [fetchTasks]))

  // Keyboard shortcuts
  useKeyboardShortcut('n', () => setModals((m) => ({ ...m, newTask: true })))
  useKeyboardShortcut('k', () => setModals((m) => ({ ...m, search: true })), { ctrl: true })

  const openModal = (name) => setModals((m) => ({ ...m, [name]: true }))
  const closeModals = () => setModals({ newTask: false, search: false, detail: null })

  const handleCreated = async (data) => {
    const task = await createTask(data)
    setTasks((prev) => [task, ...prev])
    announce(`Task "${task.title}" created`)
    toast.success('Task created!')
    return task
  }

  const handleStatusChange = async (id, status) => {
    // Optimistic update
    const prev = tasks
    setTasks((t) => t.map((task) => task.id === id ? { ...task, status } : task))
    try {
      await updateTask(id, { status })
      const task = tasks.find((t) => t.id === id)
      announce(`Task "${task?.title}" marked as ${VIEW_LABELS[status]}`)
    } catch {
      setTasks(prev)
      toast.error('Failed to update task')
    }
  }

  const handleDelete = async (id) => {
    const task = tasks.find((t) => t.id === id)
    setTasks((prev) => prev.filter((t) => t.id !== id))
    try {
      await deleteTask(id)
      announce(`Task "${task?.title}" deleted`)
      toast.success('Task deleted')
    } catch {
      fetchTasks()
      toast.error('Delete failed')
    }
  }

  const viewTasks = tasks.filter((t) => t.status === activeView)
  const taskCounts = Object.fromEntries(
    VIEWS.map((v) => [v, tasks.filter((t) => t.status === v).length])
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Skip link — first focusable element */}
      <SkipLink />

      {/* Screen reader announcements */}
      <LiveRegion message={announcement} />

      {/* Top bar (desktop only) */}
      <header
        className="hidden md:flex items-center justify-between px-6 py-3 bg-gray-900 border-b border-gray-800"
        role="banner"
      >
        <div className="flex items-center gap-2">
          <Brain size={22} className="text-blue-400" aria-hidden="true" />
          <span className="text-white font-bold">TaskMind</span>
        </div>
        <button
          onClick={() => openModal('newTask')}
          className="
            bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium
            px-4 py-2 rounded-lg min-h-[44px]
            focus:outline-none focus:ring-2 focus:ring-blue-500
          "
          aria-label="Create new task (keyboard shortcut: N)"
        >
          + New Task
        </button>
      </header>

      {/* Mobile top bar */}
      <header
        className="md:hidden flex items-center justify-between px-4 py-3 bg-gray-900 border-b border-gray-800"
        role="banner"
      >
        <div className="flex items-center gap-2">
          <Brain size={20} className="text-blue-400" aria-hidden="true" />
          <span className="text-white font-bold text-sm">TaskMind</span>
        </div>
        {user && (
          <span className="text-xs text-gray-500">{user.name}</span>
        )}
      </header>

      {/* Main content */}
      <main id="main-content" tabIndex={-1} className="pb-24 md:pb-6">
        {/* Tab switcher (mobile) */}
        <div
          className="md:hidden overflow-x-auto px-4 pt-4 pb-2"
          role="tablist"
          aria-label="Task status filter"
        >
          <div className="flex gap-2 min-w-max">
            {VIEWS.map((v) => (
              <button
                key={v}
                role="tab"
                aria-selected={activeView === v}
                aria-controls={`panel-${v}`}
                id={`tab-${v}`}
                onClick={() => setActiveView(v)}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap',
                  'min-h-[44px] transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500',
                  activeView === v
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                )}
              >
                {VIEW_LABELS[v]}
                <span
                  className={clsx(
                    'px-2 py-0.5 rounded-full text-xs',
                    activeView === v ? 'bg-blue-500' : 'bg-gray-700 text-gray-400'
                  )}
                  aria-label={`${taskCounts[v]} tasks`}
                >
                  {taskCounts[v]}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Mobile task list */}
        <div
          id={`panel-${activeView}`}
          role="tabpanel"
          aria-labelledby={`tab-${activeView}`}
          className="md:hidden px-4 py-3"
        >
          {loading ? (
            <div aria-live="polite" aria-label="Loading tasks" className="py-12 text-center">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-gray-500 text-sm">Loading tasks...</p>
            </div>
          ) : viewTasks.length === 0 ? (
            <div className="py-12 text-center" aria-label={`No ${VIEW_LABELS[activeView]} tasks`}>
              <p className="text-gray-600">No tasks here</p>
              {activeView === 'pending' && (
                <button
                  onClick={() => openModal('newTask')}
                  className="mt-3 text-blue-400 text-sm hover:text-blue-300 min-h-[44px] px-4"
                >
                  Create your first task →
                </button>
              )}
            </div>
          ) : (
            <div role="list" aria-label={`${VIEW_LABELS[activeView]} tasks`}>
              {viewTasks.map((task) => (
                <div key={task.id} role="listitem">
                  <TaskCardMobile
                    task={task}
                    onDelete={handleDelete}
                    onStatusChange={handleStatusChange}
                    onExpand={(t) => setModals((m) => ({ ...m, detail: t }))}
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Desktop: three-column layout */}
        <div className="hidden md:grid md:grid-cols-3 gap-4 p-6">
          {VIEWS.map((status) => (
            <section
              key={status}
              className="bg-gray-900 rounded-xl border border-gray-800 p-4"
              aria-labelledby={`col-${status}`}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 id={`col-${status}`} className="font-semibold text-gray-300 text-sm">
                  {VIEW_LABELS[status]}
                </h2>
                <span className="text-xs bg-gray-700 text-gray-400 rounded-full px-2 py-0.5">
                  {taskCounts[status]}
                </span>
              </div>
              <div>
                {tasks.filter((t) => t.status === status).map((task) => (
                  <TaskCardMobile
                    key={task.id}
                    task={task}
                    onDelete={handleDelete}
                    onStatusChange={handleStatusChange}
                    onExpand={(t) => setModals((m) => ({ ...m, detail: t }))}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      </main>

      {/* Task Detail Modal */}
      {modals.detail && (
        <AccessibleModal
          isOpen={!!modals.detail}
          onClose={() => setModals((m) => ({ ...m, detail: null }))}
          title={modals.detail.title}
          size="lg"
        >
          <div className="space-y-4">
            <dl className="space-y-3">
              <div>
                <dt className="text-xs text-gray-500 uppercase tracking-wide mb-1">Status</dt>
                <dd>
                  <div className="flex gap-2">
                    {VIEWS.map((s) => (
                      <button
                        key={s}
                        onClick={() => {
                          handleStatusChange(modals.detail.id, s)
                          setModals((m) => ({ ...m, detail: { ...m.detail, status: s } }))
                        }}
                        className={clsx(
                          'text-xs px-3 min-h-[40px] rounded-lg transition-colors',
                          'focus:outline-none focus:ring-2 focus:ring-blue-500',
                          modals.detail.status === s
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        )}
                        aria-pressed={modals.detail.status === s}
                      >
                        {VIEW_LABELS[s]}
                      </button>
                    ))}
                  </div>
                </dd>
              </div>

              {modals.detail.description && (
                <div>
                  <dt className="text-xs text-gray-500 uppercase tracking-wide mb-1">Description</dt>
                  <dd className="text-sm text-gray-300 leading-relaxed">{modals.detail.description}</dd>
                </div>
              )}

              {modals.detail.ai_summary && (
                <div>
                  <dt className="text-xs text-gray-500 uppercase tracking-wide mb-1">AI Summary</dt>
                  <dd className="text-sm text-purple-300">{modals.detail.ai_summary}</dd>
                </div>
              )}

              <div className="flex gap-6">
                <div>
                  <dt className="text-xs text-gray-500 uppercase tracking-wide mb-1">Priority</dt>
                  <dd className="text-sm text-white capitalize">{modals.detail.priority}</dd>
                </div>
                {modals.detail.due_date && (
                  <div>
                    <dt className="text-xs text-gray-500 uppercase tracking-wide mb-1">Due</dt>
                    <dd className="text-sm text-white">
                      {new Date(modals.detail.due_date).toLocaleDateString()}
                    </dd>
                  </div>
                )}
              </div>
            </dl>

            <button
              onClick={() => {
                handleDelete(modals.detail.id)
                setModals((m) => ({ ...m, detail: null }))
              }}
              className="
                w-full min-h-[48px] mt-4
                bg-red-900/50 hover:bg-red-800/50 border border-red-800
                text-red-300 text-sm rounded-xl
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-red-500
              "
            >
              Delete Task
            </button>
          </div>
        </AccessibleModal>
      )}

      {/* New Task Modal */}
      <TaskFormMobile
        isOpen={modals.newTask}
        onClose={() => setModals((m) => ({ ...m, newTask: false }))}
        onCreated={handleCreated}
        onAIExpand={async (title) => {
          const result = await expandTask(title)
          return result
        }}
        onAIPrioritize={async (title, desc) => {
          const result = await analyzeTask(title, desc)
          return result
        }}
      />

      {/* Search Modal */}
      {modals.search && (
        <SearchModal
          onClose={() => setModals((m) => ({ ...m, search: false }))}
          onSelectTask={(t) => {
            setModals((m) => ({ ...m, search: false, detail: t }))
          }}
        />
      )}

      {/* Mobile bottom navigation */}
      <MobileNav
        onAction={(action) => {
          if (action === 'new') openModal('newTask')
          if (action === 'search') openModal('search')
          if (action === 'stats') toast('Stats coming soon!', { icon: '📊' })
        }}
      />
    </div>
  )
}