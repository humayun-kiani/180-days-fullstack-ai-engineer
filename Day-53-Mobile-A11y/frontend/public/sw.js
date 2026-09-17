// Service Worker — PWA caching strategy

const CACHE_NAME = 'taskmind-v1'
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json'
]

// Install: pre-cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  )
})

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  )
})

// Fetch: network-first for API, cache-first for static
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // API: network only (always fresh data)
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/ws')) {
    event.respondWith(
      fetch(request).catch(() =>
        new Response(
          JSON.stringify({ error: 'Offline — API not available' }),
          { headers: { 'Content-Type': 'application/json' }, status: 503 }
        )
      )
    )
    return
  }

  // Static assets: stale-while-revalidate
  event.respondWith(
    caches.open(CACHE_NAME).then((cache) =>
      cache.match(request).then((cached) => {
        const fetchPromise = fetch(request).then((response) => {
          if (response.ok) {
            cache.put(request, response.clone())
          }
          return response
        })
        // Return cached immediately while fetching update in background
        return cached || fetchPromise
      })
    )
  )
})

// Background sync for offline task creation (simplified)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-tasks') {
    // In production: read from IndexedDB, replay API calls
    console.log('Background sync: tasks')
  }
})