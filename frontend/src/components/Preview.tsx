import type { Picture } from '../api/types'
import { PreviewItem } from './PreviewItem'

const DEFAULT_PAGE_SIZE = 25

type Props = {
  pictures: Picture[]
  page: number
  onPageChange: (page: number) => void
  pageSize?: number
}

export function Preview({
  pictures,
  page,
  onPageChange,
  pageSize = DEFAULT_PAGE_SIZE,
}: Props) {
  const hasPrev = page > 1
  const hasNext = pictures.length >= pageSize

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col bg-canvas/40">
      <div className="min-h-0 flex-1 overflow-auto px-4 py-4 library:px-6">
        <h2 className="text-lg font-semibold text-ink">Preview</h2>
        {pictures.length === 0 ? (
          <div className="mt-6 flex flex-col items-center justify-center rounded-md border border-dashed border-line bg-surface px-4 py-12 text-center">
            <p className="text-base font-semibold text-ink">No photos</p>
            <p className="mt-1 text-sm text-ink-muted">
              Scan photos or clear filters to see previews here.
            </p>
          </div>
        ) : (
          <div className="mt-4 flex flex-wrap content-start gap-3">
            {pictures.map((picture) => (
              <PreviewItem key={picture.id} picture={picture} />
            ))}
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-line bg-panel px-4 py-3 library:px-6">
        <div className="flex items-center justify-between gap-3">
          <button
            type="button"
            disabled={!hasPrev}
            onClick={() => onPageChange(page - 1)}
            className={[
              'rounded px-3 py-1.5 text-sm font-semibold transition-colors',
              hasPrev
                ? 'bg-surface text-ink ring-1 ring-line hover:bg-accent-soft'
                : 'cursor-not-allowed bg-surface/60 text-ink-muted opacity-50',
            ].join(' ')}
          >
            Previous
          </button>

          <span className="text-sm font-medium text-ink-muted" aria-live="polite">
            Page {page}
          </span>

          <button
            type="button"
            disabled={!hasNext}
            onClick={() => onPageChange(page + 1)}
            className={[
              'rounded px-3 py-1.5 text-sm font-semibold transition-colors',
              hasNext
                ? 'bg-accent text-on-accent hover:brightness-110'
                : 'cursor-not-allowed bg-surface/60 text-ink-muted opacity-50',
            ].join(' ')}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
