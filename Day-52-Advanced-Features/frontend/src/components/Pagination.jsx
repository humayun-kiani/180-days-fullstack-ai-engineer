// frontend/src/components/Pagination.jsx
import { ChevronLeft, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

export default function Pagination({ page, pages, total, perPage, onPageChange }) {
  if (pages <= 1) return null

  const from = (page - 1) * perPage + 1
  const to = Math.min(page * perPage, total)

  const pageNumbers = []
  const delta = 2
  for (let i = Math.max(1, page - delta); i <= Math.min(pages, page + delta); i++) {
    pageNumbers.push(i)
  }

  return (
    <div className="flex items-center justify-between mt-4">
      <span className="text-xs text-gray-500">
        {from}–{to} of {total} tasks
      </span>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft size={16} />
        </button>

        {pageNumbers[0] > 1 && (
          <>
            <button onClick={() => onPageChange(1)}
              className="px-2.5 py-1 rounded text-xs text-gray-400 hover:text-white hover:bg-gray-700">
              1
            </button>
            {pageNumbers[0] > 2 && <span className="text-gray-600 text-xs">…</span>}
          </>
        )}

        {pageNumbers.map((p) => (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={clsx(
              'px-2.5 py-1 rounded text-xs transition-colors',
              p === page
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            )}
          >
            {p}
          </button>
        ))}

        {pageNumbers[pageNumbers.length - 1] < pages && (
          <>
            {pageNumbers[pageNumbers.length - 1] < pages - 1 && (
              <span className="text-gray-600 text-xs">…</span>
            )}
            <button onClick={() => onPageChange(pages)}
              className="px-2.5 py-1 rounded text-xs text-gray-400 hover:text-white hover:bg-gray-700">
              {pages}
            </button>
          </>
        )}

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page === pages}
          className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}