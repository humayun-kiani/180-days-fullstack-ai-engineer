// frontend/src/__tests__/unit/analyzeTitle.test.js
// Pure function tests — no React needed

import { describe, it, expect } from 'vitest'

// Utility function to extract from TaskForm logic
function guessPriorityFromTitle(title) {
  const t = title.toLowerCase()
  if (['urgent', 'critical', 'asap', 'emergency', 'p0', 'outage']
      .some(w => t.includes(w))) return 'urgent'
  if (['fix', 'bug', 'error', 'security', 'breach', 'deadline']
      .some(w => t.includes(w))) return 'high'
  if (['add', 'implement', 'create', 'build', 'update', 'improve']
      .some(w => t.includes(w))) return 'medium'
  return 'low'
}

function truncateTitle(title, maxLength = 500) {
  if (title.length <= maxLength) return title
  return title.slice(0, maxLength - 3) + '...'
}

function isValidPriority(priority) {
  return ['urgent', 'high', 'medium', 'low'].includes(priority)
}

describe('guessPriorityFromTitle', () => {
  it('returns urgent for URGENT keyword', () => {
    expect(guessPriorityFromTitle('URGENT: fix prod')).toBe('urgent')
  })

  it('returns urgent for critical keyword', () => {
    expect(guessPriorityFromTitle('Critical security issue')).toBe('urgent')
  })

  it('returns urgent for outage keyword', () => {
    expect(guessPriorityFromTitle('service outage in production')).toBe('urgent')
  })

  it('returns high for fix keyword', () => {
    expect(guessPriorityFromTitle('Fix login authentication')).toBe('high')
  })

  it('returns high for bug keyword', () => {
    expect(guessPriorityFromTitle('Resolve payment processing bug')).toBe('high')
  })

  it('returns medium for add keyword', () => {
    expect(guessPriorityFromTitle('Add export functionality')).toBe('medium')
  })

  it('returns medium for implement keyword', () => {
    expect(guessPriorityFromTitle('Implement dark mode')).toBe('medium')
  })

  it('returns low for unrecognized keywords', () => {
    expect(guessPriorityFromTitle('Review design mockups')).toBe('low')
  })

  it('is case-insensitive', () => {
    expect(guessPriorityFromTitle('URGENT: PRODUCTION DOWN')).toBe('urgent')
    expect(guessPriorityFromTitle('Fix Bug')).toBe('high')
  })
})

describe('truncateTitle', () => {
  it('returns title unchanged when under limit', () => {
    const title = 'Short title'
    expect(truncateTitle(title, 500)).toBe(title)
  })

  it('truncates at max length', () => {
    const longTitle = 'x'.repeat(510)
    const result = truncateTitle(longTitle, 500)
    expect(result.length).toBe(500)
  })

  it('adds ellipsis when truncated', () => {
    const result = truncateTitle('x'.repeat(510), 500)
    expect(result.endsWith('...')).toBe(true)
  })

  it('handles exact length', () => {
    const title = 'x'.repeat(500)
    expect(truncateTitle(title, 500)).toBe(title)
  })
})

describe('isValidPriority', () => {
  it.each(['urgent', 'high', 'medium', 'low'])(
    'returns true for %s',
    (priority) => {
      expect(isValidPriority(priority)).toBe(true)
    }
  )

  it.each(['critical', 'normal', 'severe', '', 'URGENT'])(
    'returns false for %s',
    (priority) => {
      expect(isValidPriority(priority)).toBe(false)
    }
  )
})