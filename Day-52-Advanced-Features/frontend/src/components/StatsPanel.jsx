// frontend/src/components/StatsPanel.jsx
import { useEffect, useState } from 'react'
import { BarChart3, TrendingUp, AlertTriangle, CheckCircle, Loader } from 'lucide-react'
import client from '../api/client'
import clsx from 'clsx'

const HEALTH_CONFIG = {
  healthy: { color: 'text-green-400', icon: CheckCircle, label: 'Healthy' },
  ok: { color: 'text-blue-400', icon: TrendingUp, label: 'OK' },
  warning: { color: 'text-orange-400', icon: AlertTriangle, label: 'Warning' },
  critical: { color: 'text-red-400', icon: AlertTriangle, label: 'Critical' },
  no_data: { color: 'text-gray-400', icon: BarChart3, label: 'No Data' }
}

export default function StatsPanel({ visible }) {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!visible || stats) return
    setLoading(true)
    client.get('/stats')
      .then((r) => setStats(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [visible, stats])

  // Refresh when visible changes to true
  useEffect(() => {
    if (visible) setStats(null)
  }, [visible])

  if (!visible) return null

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 flex items-center justify-center">
        <Loader size={20} className="animate-spin text-gray-400" />
      </div>
    )
  }

  if (!stats) return null

  const health = HEALTH_CONFIG[stats.health?.score] || HEALTH_CONFIG.ok
  const HealthIcon = health.icon

  return (
    <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 size={18} className="text-blue-400" />
          <h2 className="text-white font-semibold text-sm">Statistics</h2>
        </div>
        <div className={clsx('flex items-center gap-1 text-xs', health.color)}>
          <HealthIcon size={12} />
          {health.label}
        </div>
      </div>

      {/* Overview grid */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        {[
          { label: 'Total', value: stats.overview?.total, color: 'text-white' },
          { label: 'Done', value: stats.overview?.done, color: 'text-green-400' },
          { label: 'In Progress', value: stats.overview?.in_progress, color: 'text-blue-400' },
          { label: 'Overdue', value: stats.overview?.overdue, color: 'text-red-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-gray-900 rounded-lg p-3 text-center">
            <div className={clsx('text-xl font-bold', color)}>{value ?? 0}</div>
            <div className="text-xs text-gray-500 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Completion rate */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Completion</span>
          <span>{stats.overview?.completion_rate_pct}%</span>
        </div>
        <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all"
            style={{ width: `${stats.overview?.completion_rate_pct || 0}%` }}
          />
        </div>
      </div>

      {/* Priority breakdown */}
      <div className="space-y-1 mb-4">
        <p className="text-xs text-gray-500 mb-2">By priority</p>
        {Object.entries(stats.by_priority || {}).map(([p, count]) => (
          <div key={p} className="flex items-center gap-2">
            <span className={clsx('text-xs capitalize w-14', {
              'text-red-400': p === 'urgent',
              'text-orange-400': p === 'high',
              'text-blue-400': p === 'medium',
              'text-gray-400': p === 'low'
            })}>{p}</span>
            <div className="flex-1 h-1 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full', {
                  'bg-red-500': p === 'urgent',
                  'bg-orange-500': p === 'high',
                  'bg-blue-500': p === 'medium',
                  'bg-gray-500': p === 'low'
                })}
                style={{
                  width: `${stats.overview?.total > 0 ? count / stats.overview.total * 100 : 0}%`
                }}
              />
            </div>
            <span className="text-xs text-gray-500 w-6 text-right">{count}</span>
          </div>
        ))}
      </div>

      {/* This week */}
      <div className="bg-gray-900 rounded-lg p-3">
        <p className="text-xs text-gray-500 mb-2">This week</p>
        <div className="flex justify-between text-sm">
          <div>
            <div className="text-white font-medium">{stats.this_week?.created}</div>
            <div className="text-xs text-gray-500">created</div>
          </div>
          <div className="text-right">
            <div className="text-green-400 font-medium">{stats.this_week?.completed}</div>
            <div className="text-xs text-gray-500">completed</div>
          </div>
        </div>
      </div>

      {/* Issues */}
      {stats.health?.issues?.length > 0 && (
        <div className="mt-3 space-y-1">
          {stats.health.issues.map((issue, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-orange-400">
              <AlertTriangle size={10} className="mt-0.5 shrink-0" />
              {issue}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}