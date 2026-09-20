// frontend/src/__tests__/components/TaskCard.test.jsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TaskCard from '../../components/TaskCard'

// Mock API modules
vi.mock('../../api/tasks', () => ({
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
}))
vi.mock('../../api/ai', () => ({
  analyzeTask: vi.fn(),
}))

const sampleTask = {
  id: 'task-123',
  title: 'Fix login authentication bug',
  description: 'Users with special characters in passwords fail to log in',
  status: 'pending',
  priority: 'high',
  owner_id: 'user-456',
  ai_summary: null,
  ai_priority: null,
  due_date: null,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
}

describe('TaskCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders task title', () => {
      render(<TaskCard task={sampleTask} />)
      expect(screen.getByText('Fix login authentication bug')).toBeInTheDocument()
    })

    it('renders priority badge', () => {
      render(<TaskCard task={sampleTask} />)
      expect(screen.getByText('high')).toBeInTheDocument()
    })

    it('renders status', () => {
      render(<TaskCard task={sampleTask} />)
      expect(screen.getByText('Pending')).toBeInTheDocument()
    })

    it('does not show description initially (collapsed)', () => {
      render(<TaskCard task={sampleTask} />)
      expect(screen.queryByText(sampleTask.description)).not.toBeInTheDocument()
    })

    it('shows description after expanding', async () => {
      const user = userEvent.setup()
      render(<TaskCard task={sampleTask} />)
      await user.click(screen.getByRole('button', { name: /expand|chevron/i }))
      expect(screen.getByText(sampleTask.description)).toBeInTheDocument()
    })

    it('applies correct priority color for urgent', () => {
      const urgentTask = { ...sampleTask, priority: 'urgent' }
      const { container } = render(<TaskCard task={urgentTask} />)
      expect(container.firstChild).toHaveClass(/red/)
    })
  })

  describe('Status change', () => {
    it('calls onUpdate when status changes', async () => {
      const { updateTask } = await import('../../api/tasks')
      updateTask.mockResolvedValue({ ...sampleTask, status: 'in_progress' })

      const user = userEvent.setup()
      const onUpdate = vi.fn()
      render(<TaskCard task={sampleTask} onUpdate={onUpdate} />)

      // Expand to see status buttons
      await user.click(screen.getAllByRole('button')[0])
      await user.click(screen.getByRole('button', { name: /in progress/i }))

      await waitFor(() => {
        expect(updateTask).toHaveBeenCalledWith(sampleTask.id, { status: 'in_progress' })
      })
    })
  })

  describe('Deletion', () => {
    it('calls onDelete when confirmed', async () => {
      const { deleteTask } = await import('../../api/tasks')
      deleteTask.mockResolvedValue({})
      vi.spyOn(window, 'confirm').mockReturnValue(true)

      const user = userEvent.setup()
      const onDelete = vi.fn()
      render(<TaskCard task={sampleTask} onDelete={onDelete} />)

      await user.click(screen.getByRole('button', { name: /delete|trash/i }))

      await waitFor(() => {
        expect(deleteTask).toHaveBeenCalledWith(sampleTask.id)
        expect(onDelete).toHaveBeenCalledWith(sampleTask.id)
      })
    })

    it('does NOT delete when user cancels confirm', async () => {
      const { deleteTask } = await import('../../api/tasks')
      vi.spyOn(window, 'confirm').mockReturnValue(false)

      const user = userEvent.setup()
      render(<TaskCard task={sampleTask} />)

      await user.click(screen.getByRole('button', { name: /delete|trash/i }))
      expect(deleteTask).not.toHaveBeenCalled()
    })
  })

  describe('AI Analysis', () => {
    it('shows AI analyze button when expanded', async () => {
      const user = userEvent.setup()
      render(<TaskCard task={sampleTask} />)
      await user.click(screen.getAllByRole('button')[0])
      expect(screen.getByText(/ai.*analyz/i)).toBeInTheDocument()
    })

    it('shows AI summary if task has one', () => {
      const taskWithAI = {
        ...sampleTask,
        ai_summary: 'High priority auth issue needing immediate attention'
      }
      const { container } = render(<TaskCard task={taskWithAI} />)
      // Expand to see summary
      fireEvent.click(container.querySelectorAll('button')[0])
      expect(screen.getByText('High priority auth issue needing immediate attention')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('delete button has accessible label', () => {
      render(<TaskCard task={sampleTask} />)
      const deleteBtn = screen.getByRole('button', { name: /delete|trash|remove/i })
      expect(deleteBtn).toBeInTheDocument()
    })

    it('expand button is keyboard accessible', async () => {
      render(<TaskCard task={sampleTask} />)
      const expandBtn = screen.getAllByRole('button')[0]
      expandBtn.focus()
      expect(document.activeElement).toBe(expandBtn)
    })
  })
})