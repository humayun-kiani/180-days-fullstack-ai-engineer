// frontend/src/hooks/useWebSocket.js
import { useEffect, useRef, useCallback } from 'react'
import useAuthStore from '../store/authStore'

export function useWebSocket(onMessage) {
  const wsRef = useRef(null)
  const token = useAuthStore((s) => s.token)

  const connect = useCallback(() => {
    if (!token) return
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${window.location.host}/ws?token=${token}`
    const ws = new WebSocket(url)

    ws.onopen = () => console.log('WS connected')
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type !== 'keepalive' && msg.type !== 'pong') {
          onMessage?.(msg)
        }
        // Respond to keepalive
        if (msg.type === 'keepalive') {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      } catch (err) {
        console.error('WS parse error:', err)
      }
    }
    ws.onclose = () => {
      console.log('WS disconnected, reconnecting...')
      setTimeout(connect, 3000)
    }
    ws.onerror = (e) => console.error('WS error:', e)
    wsRef.current = ws
  }, [token, onMessage])

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [connect])
}