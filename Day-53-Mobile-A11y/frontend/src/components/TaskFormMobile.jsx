// frontend/src/components/TaskFormMobile.jsx
import { useState, useRef, useEffect } from 'react'
import { Plus, Sparkles, Loader, X } from 'lucide-react'
import clsx from 'clsx'
import AccessibleModal from './AccessibleModal'

const PRIORITIES = ['urgent', 'high', 'medium', 'low']
const PRIORITY_COLORS = {
  urgent: 'bg-red-600 text-white',
  high:   'bg-orange-600 text-white',
  medium: 'bg-blue-600 text-white',
  low:    'bg-gray-600 text-white'
}

/**
 * Mobile-optimized task creation form.
 *
 * Full-screen modal on mobile, inline on desktop.
 * Large inputs and tap targets.
 * Full accessibility with ARIA labels.
 */
export default function TaskFormMobile({ isOpen, onClose, onCreated, onAIExpand, onAIPrioritize }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('medium')
  const [submitting, setSubmitting] = useState(false)
  const [aiLoading, setAiLoading] = useState(null)
  const [errors, setErrors] = useState({})
  const titleRef = useRef(null)

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => titleRef.current?.focus(), 100)
    } else {
      setTitle('')
      setDescription('')
      setPriority('medium')
      setErrors({})
    }
  }, [isOpen])

  const validate = () => {
    const errs = {}
    if (!title.trim()) errs.title = 'Title is required'
    if (title.length > 500) errs.title = 'Title must be 500 characters or less'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setSubmitting(true)
    try {
      await onCreated?.({ title: title.trim(), description, priority })
      onClose()
    } catch (err) {
      setErrors({ submit: 'Failed to create task. Please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  const handleAIExpand = async () => {
    if (!title.trim()) {
      setErrors({ title: 'Enter a title to expand' })
      return
    }
    setAiLoading('expand')
    try {
      const result = await onAIExpand?.(title)
      if (result) {
        setDescription(result.description)
        setPriority(result.suggested_priority)
      }
    } finally {
      setAiLoading(null)
    }
  }

  const handleAIPrioritize = async () => {
    if (!title.trim()) return
    setAiLoading('prioritize')
    try {
      const result = await onAIPrioritize?.(title, description)
      if (result) setPriority(result.suggested_priority)
    } finally {
      setAiLoading(null)
    }
  }

  return (
    <AccessibleModal isOpen={isOpen} onClose={onClose} title="New Task" size="md">
      <form onSubmit={handleSubmit} noValidate>
        {/* Title field */}
        <div className="mb-4">
          <label
            htmlFor="task-title"
            className="block text-sm font-medium text-gray-300 mb-1.5"
          >
            Title <span aria-hidden="true" className="text-red-400">*</span>
            <span className="sr-only">(required)</span>
          </label>
          <input
            ref={titleRef}
            id="task-title"
            type="text"
            value={title}
            onChange={(e) => { setTitle(e.target.value); setErrors({}) }}
            placeholder="What needs to be done?"
            required
            maxLength={500}
            aria-required="true"
            aria-invalid={!!errors.title}
            aria-describedby={errors.title ? 'title-error' : 'title-hint'}
            className={clsx(
              'w-full bg-gray-900 border rounded-xl px-4 py-3.5',
              'text-white text-base placeholder-gray-500',
              'focus:outline-none focus:ring-2',
              errors.title
                ? 'border-red-500 focus:ring-red-500'
                : 'border-gray-700 focus:ring-blue-500'
            )}
          />
          <div className="flex justify-between mt-1">
            {errors.title ? (
              <span id="title-error" role="alert" className="text-xs text-red-400">
                {errors.title}
              </span>
            ) : (
              <span id="title-hint" className="text-xs text-gray-600">
                Be specific and action-oriented
              </span>
            )}
            <span className="text-xs text-gray-600" aria-live="polite">
              {title.length}/500
            </span>
          </div>
        </div>

        {/* Description */}
        <div className="mb-4">
          <label htmlFor="task-description" className="block text-sm font-medium text-gray-300 mb-1.5">
            Description
            <span className="text-gray-500 text-xs font-normal ml-2">(optional)</span>
          </label>
          <textarea
            id="task-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add more context..."
            rows={3}
            className="
              w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3.5
              text-white text-base placeholder-gray-500 resize-none
              focus:outline-none focus:ring-2 focus:ring-blue-500
            "
          />
        </div>

        {/* AI buttons */}
        <div
          className="flex gap-3 mb-4"
          role="group"
          aria-label="AI assistance tools"
        >
          <button
            type="button"
            onClick={handleAIExpand}
            disabled={!!aiLoading || !title.trim()}
            className="
              flex items-center gap-1.5 text-sm text-purple-400
              hover:text-purple-300 disabled:opacity-40
              min-h-[44px] px-3 rounded-lg
              focus:outline-none focus:ring-2 focus:ring-purple-500
              transition-colors
            "
            aria-label="Use AI to expand task title into a description"
          >
            {aiLoading === 'expand'
              ? <Loader size={14} className="animate-spin" aria-hidden="true" />
              : <Sparkles size={14} aria-hidden="true" />}
            AI Expand
          </button>

          <button
            type="button"
            onClick={handleAIPrioritize}
            disabled={!!aiLoading || !title.trim()}
            className="
              flex items-center gap-1.5 text-sm text-purple-400
              hover:text-purple-300 disabled:opacity-40
              min-h-[44px] px-3 rounded-lg
              focus:outline-none focus:ring-2 focus:ring-purple-500
              transition-colors
            "
            aria-label="Use AI to suggest a priority level for this task"
          >
            {aiLoading === 'prioritize'
              ? <Loader size={14} className="animate-spin" aria-hidden="true" />
              : <Sparkles size={14} aria-hidden="true" />}
            AI Prioritize
          </button>
        </div>

        {/* Priority selector */}
        <fieldset className="mb-6">
          <legend className="text-sm font-medium text-gray-300 mb-2">
            Priority
          </legend>
          <div className="grid grid-cols-4 gap-2" role="radiogroup">
            {PRIORITIES.map((p) => (
              <label
                key={p}
                className={clsx(
                  'flex items-center justify-center min-h-[44px]',
                  'rounded-xl text-sm font-medium capitalize cursor-pointer',
                  'transition-all border-2',
                  priority === p
                    ? `${PRIORITY_COLORS[p]} border-transparent`
                    : 'border-gray-700 text-gray-400 hover:border-gray-500'
                )}
              >
                <input
                  type="radio"
                  name="priority"
                  value={p}
                  checked={priority === p}
                  onChange={() => setPriority(p)}
                  className="sr-only"
                />
                {p}
              </label>
            ))}
          </div>
        </fieldset>

        {/* Submit error */}
        {errors.submit && (
          <div role="alert" className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg">
            <p className="text-sm text-red-300">{errors.submit}</p>
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting || !title.trim()}
          className="
            w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50
            text-white font-semibold py-4 rounded-xl text-base
            transition-colors
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800
            flex items-center justify-center gap-2
            min-h-[56px]
          "
          aria-busy={submitting}
        >
          {submitting && <Loader size={18} className="animate-spin" aria-hidden="true" />}
          {submitting ? 'Creating task...' : 'Create Task'}
        </button>
      </form>
    </AccessibleModal>
  )
}