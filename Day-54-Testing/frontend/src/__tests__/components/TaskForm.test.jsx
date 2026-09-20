// frontend/src/__tests__/components/TaskForm.test.jsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TaskForm from '../../components/TaskForm'

vi.mock('../../api/tasks', () => ({
  createTask: vi.fn(),
}))
vi.mock('../../api/ai', () => ({
  analyzeTask: vi.fn(),
  expandTask: vi.fn(),
}))

describe('TaskForm', () => {
  beforeEach(() => { vi.clearAllMocks() })

  describe('Rendering', () => {
    it('renders title input', () => {
      render(<TaskForm />)
      expect(screen.getByPlaceholderText(/task title/i)).toBeInTheDocument()
    })

    it('renders priority selector', () => {
      render(<TaskForm />)
      expect(screen.getByText('urgent')).toBeInTheDocument()
      expect(screen.getByText('high')).toBeInTheDocument()
      expect(screen.getByText('medium')).toBeInTheDocument()
      expect(screen.getByText('low')).toBeInTheDocument()
    })

    it('renders submit button', () => {
      render(<TaskForm />)
      expect(screen.getByRole('button', { name: /create task/i })).toBeInTheDocument()
    })

    it('submit button disabled when title empty', () => {
      render(<TaskForm />)
      const btn = screen.getByRole('button', { name: /create task/i })
      expect(btn).toBeDisabled()
    })
  })

  describe('Form submission', () => {
    it('submits with title and default priority', async () => {
      const { createTask } = await import('../../api/tasks')
      createTask.mockResolvedValue({ id: '1', title: 'New task', status: 'pending', priority: 'medium' })

      const user = userEvent.setup()
      const onCreated = vi.fn()
      render(<TaskForm onCreated={onCreated} />)

      await user.type(screen.getByPlaceholderText(/task title/i), 'New task')
      await user.click(screen.getByRole('button', { name: /create task/i }))

      await waitFor(() => {
        expect(createTask).toHaveBeenCalledWith(expect.objectContaining({
          title: 'New task',
          priority: 'medium'
        }))
      })
    })

    it('clears form after successful creation', async () => {
      const { createTask } = await import('../../api/tasks')
      createTask.mockResolvedValue({ id: '1', title: 'Task', status: 'pending' })

      const user = userEvent.setup()
      render(<TaskForm onCreated={vi.fn()} />)

      const input = screen.getByPlaceholderText(/task title/i)
      await user.type(input, 'My task')
      await user.click(screen.getByRole('button', { name: /create task/i }))

      await waitFor(() => {
        expect(input).toHaveValue('')
      })
    })

    it('selects clicked priority', async () => {
      const { createTask } = await import('../../api/tasks')
      createTask.mockResolvedValue({ id: '1', title: 'Task', status: 'pending' })

      const user = userEvent.setup()
      render(<TaskForm onCreated={vi.fn()} />)

      await user.type(screen.getByPlaceholderText(/task title/i), 'Urgent task')
      await user.click(screen.getByRole('button', { name: /^urgent$/i }))
      await user.click(screen.getByRole('button', { name: /create task/i }))

      await waitFor(() => {
        expect(createTask).toHaveBeenCalledWith(expect.objectContaining({
          priority: 'urgent'
        }))
      })
    })
  })

  describe('AI features', () => {
    it('AI Expand button is present', () => {
      render(<TaskForm />)
      expect(screen.getByText(/ai expand/i)).toBeInTheDocument()
    })

    it('AI Prioritize button is present', () => {
      render(<TaskForm />)
      expect(screen.getByText(/ai prioritize/i)).toBeInTheDocument()
    })

    it('calls expandTask when AI Expand clicked', async () => {
      const { expandTask } = await import('../../api/ai')
      expandTask.mockResolvedValue({
        description: 'Expanded description',
        suggested_priority: 'high',
        suggested_tags: []
      })

      const user = userEvent.setup()
      render(<TaskForm />)

      await user.type(screen.getByPlaceholderText(/task title/i), 'Add dark mode')
      await user.click(screen.getByText(/ai expand/i))

      await waitFor(() => {
        expect(expandTask).toHaveBeenCalledWith('Add dark mode')
      })
    })
  })
})