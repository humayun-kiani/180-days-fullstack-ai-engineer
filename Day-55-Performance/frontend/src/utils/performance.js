// frontend/src/utils/performance.js
// Frontend performance utilities

/**
 * Measure component render time.
 * Wrap around expensive components during development.
 */
export function measureRender(componentName, renderFn) {
  if (process.env.NODE_ENV !== 'development') return renderFn()
  const start = performance.now()
  const result = renderFn()
  const end = performance.now()
  if (end - start > 16) {  // > 1 frame (16ms at 60fps)
    console.warn(`⚠️ Slow render: ${componentName} took ${(end - start).toFixed(1)}ms`)
  }
  return result
}


/**
 * Measure time until page is interactive.
 * Call once after app loads.
 */
export function measureTTI() {
  if (!window.performance) return

  const navigationEntry = performance.getEntriesByType('navigation')[0]
  if (!navigationEntry) return

  const metrics = {
    // Time to First Byte
    ttfb: Math.round(navigationEntry.responseStart - navigationEntry.requestStart),
    // DOM Content Loaded
    dcl: Math.round(navigationEntry.domContentLoadedEventEnd - navigationEntry.startTime),
    // Time to Interactive (approximate)
    tti: Math.round(navigationEntry.domInteractive - navigationEntry.startTime),
    // Full page load
    load: Math.round(navigationEntry.loadEventEnd - navigationEntry.startTime),
  }

  console.table(metrics)

  // Flag slow metrics
  if (metrics.tti > 3000) console.warn('⚠️ Slow TTI:', metrics.tti + 'ms (target < 3000ms)')
  if (metrics.ttfb > 600) console.warn('⚠️ Slow TTFB:', metrics.ttfb + 'ms (target < 600ms)')

  return metrics
}


/**
 * Mark React component re-renders for profiling.
 * Paste at top of component render body during debugging.
 */
export function useRenderCount(componentName) {
  const count = useRef(0)
  count.current++
  if (process.env.NODE_ENV === 'development' && count.current > 10) {
    console.warn(`⚠️ ${componentName} has rendered ${count.current} times`)
  }
  return count.current
}


/**
 * Bundle size reporter.
 * In production: use webpack-bundle-analyzer or vite-bundle-visualizer
 *
 * CLI: npx vite-bundle-visualizer
 * Tells you: which packages are largest, duplicates, unused code
 *
 * Common issues:
 * - moment.js (70KB) → use date-fns (2KB for what you use)
 * - lodash (69KB) → import specific functions
 * - lucide-react (thousands of icons) → tree-shaking should handle this
 */
export const BUNDLE_TIPS = {
  "lucide-react": "Use named imports: import { Brain } from 'lucide-react'",
  "date-fns": "Import only what you use: import { format } from 'date-fns'",
  "axios": "Consider fetch() for simple use cases to save ~14KB",
  "zustand": "Already tiny (2KB) — no optimization needed"
}


/**
 * Web Vitals measurement (Core Web Vitals for Lighthouse score).
 * In production: send to analytics.
 */
export async function measureWebVitals() {
  if (!('PerformanceObserver' in window)) return

  // Largest Contentful Paint (LCP) — target < 2.5s
  new PerformanceObserver((list) => {
    const entries = list.getEntries()
    const lcp = entries[entries.length - 1]
    const lcpMs = Math.round(lcp.renderTime || lcp.loadTime)
    console.log('LCP:', lcpMs + 'ms', lcpMs < 2500 ? '✅' : '❌ (target < 2500ms)')
  }).observe({ entryTypes: ['largest-contentful-paint'] })

  // Cumulative Layout Shift (CLS) — target < 0.1
  let clsScore = 0
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (!entry.hadRecentInput) clsScore += entry.value
    }
    console.log('CLS:', clsScore.toFixed(3), clsScore < 0.1 ? '✅' : '❌ (target < 0.1)')
  }).observe({ entryTypes: ['layout-shift'] })
}