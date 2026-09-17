// frontend/src/components/MobileNav.jsx
import { LayoutDashboard, Plus, BarChart3, User, Search } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import clsx from 'clsx'

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: 'Board', path: '/board' },
  { icon: Search, label: 'Search', action: 'search' },
  { icon: Plus, label: 'New Task', action: 'new', primary: true },
  { icon: BarChart3, label: 'Stats', action: 'stats' },
  { icon: User, label: 'Profile', path: '/profile' },
]

/**
 * Mobile bottom navigation bar.
 *
 * Replaces the top nav on small screens.
 * Each item has a large tap target (48px minimum).
 */
export default function MobileNav({ onAction }) {
  const location = useLocation()
  const navigate = useNavigate()

  const handleTap = (item) => {
    if (item.path) {
      navigate(item.path)
    } else if (item.action) {
      onAction?.(item.action)
    }
  }

  return (
    <nav
      className="
        fixed bottom-0 left-0 right-0 z-40
        bg-gray-900 border-t border-gray-800
        flex items-stretch
        safe-area-inset-bottom
        md:hidden
      "
      role="navigation"
      aria-label="Mobile navigation"
    >
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon
        const isActive = item.path && location.pathname === item.path

        return (
          <button
            key={item.label}
            onClick={() => handleTap(item)}
            className={clsx(
              'flex-1 flex flex-col items-center justify-center gap-1',
              'min-h-[64px] py-2 px-1',  // 64px tap target
              'transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500',
              item.primary
                ? 'text-white'
                : isActive
                ? 'text-blue-400'
                : 'text-gray-500 hover:text-gray-300'
            )}
            aria-label={item.label}
            aria-current={isActive ? 'page' : undefined}
          >
            {item.primary ? (
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center -mt-6 shadow-lg">
                <Icon size={22} aria-hidden="true" />
              </div>
            ) : (
              <>
                <Icon size={22} aria-hidden="true" />
                <span className="text-[10px] font-medium">{item.label}</span>
              </>
            )}
          </button>
        )
      })}
    </nav>
  )
}