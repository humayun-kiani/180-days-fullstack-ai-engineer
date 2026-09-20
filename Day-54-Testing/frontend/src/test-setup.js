// frontend/src/test-setup.js
import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock react-router-dom for components that use useNavigate
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/board' }),
  }
})

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
  Toaster: () => null,
}))

// Suppress specific console errors in tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
       args[0].includes('act(...)'))
    ) return
    originalError(...args)
  }
})
afterAll(() => { console.error = originalError })