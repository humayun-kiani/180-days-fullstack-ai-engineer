// frontend/src/store/authStore.js
import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),

  setAuth: (user, token) => {
    localStorage.setItem('access_token', token)
    set({ user, token })
  },

  logout: () => {
    localStorage.removeItem('access_token')
    set({ user: null, token: null })
  },
}))

export default useAuthStore