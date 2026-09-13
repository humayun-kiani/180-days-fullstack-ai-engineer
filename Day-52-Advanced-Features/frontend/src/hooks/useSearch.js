// frontend/src/hooks/useSearch.js
import { useState, useCallback, useRef } from 'react'
import client from '../api/client'

export function useSearch() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [query, setQuery] = useState('')
  const debounceRef = useRef(null)

  const search = useCallback((q, params = {}) => {
    setQuery(q)
    clearTimeout(debounceRef.current)

    if (!q.trim()) {
      setResults([])
      return
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const response = await client.get('/search', {
          params: { q, ...params }
        })
        setResults(response.data.tasks || [])
      } catch (err) {
        console.error('Search error:', err)
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 250)   // 250ms debounce
  }, [])

  const clearSearch = useCallback(() => {
    setQuery('')
    setResults([])
    clearTimeout(debounceRef.current)
  }, [])

  return { results, loading, query, search, clearSearch }
}