// frontend/src/App.jsx — Day 53
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useEffect } from 'react'
import LoginPage from './pages/LoginPage'
import BoardPageMobile from './pages/BoardPageMobile'
import useAuthStore from './store/authStore'

function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  return token ? children : <Navigate to="/login" replace />
}

function PWASetup() {
  useEffect(() => {
    // Register service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw.js')
        .then(() => console.log('SW registered'))
        .catch((err) => console.warn('SW failed:', err))
    }
  }, [])
  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <PWASetup />
      <Toaster
        position="top-center"
        toastOptions={{
          style: {
            background: '#1f2937',
            color: '#f9fafb',
            border: '1px solid #374151',
            borderRadius: '12px',
          },
          duration: 3000,
        }}
      />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/board" element={
          <ProtectedRoute>
            <BoardPageMobile />
          </ProtectedRoute>
        } />
        <Route path="/" element={<Navigate to="/board" replace />} />
      </Routes>
    </BrowserRouter>
  )
}