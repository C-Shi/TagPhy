import { Link } from 'react-router-dom'
import type { TagResponse } from '../api/types'

type Props = {
  tag: TagResponse
  selected: boolean
  onToggleSelect: (tagId: number) => void
}

export function TagCard({ tag, selected, onToggleSelect }: Props) {
  const photoLabel =
    tag.photo_count === 1 ? '1 photo' : `${tag.photo_count} photos`
  const childLabel =
    tag.children.length === 1
      ? '1 child'
      : `${tag.children.length} children`

  return (
    <div
      className={[
        'flex items-start gap-2 border-l-2 py-2.5 pl-1.5 pr-1 transition-colors',
        selected
          ? 'border-l-accent bg-accent-soft/80'
          : 'border-l-transparent hover:bg-surface/80',
      ].join(' ')}
    >
      <label
        className="flex shrink-0 cursor-pointer flex-col items-center gap-0.5 pt-0.5"
        title="Add to filter (AND with other selected tags)"
      >
        <input
          type="checkbox"
          checked={selected}
          onChange={() => onToggleSelect(tag.id)}
          className="h-4 w-4 cursor-pointer accent-accent"
          aria-label={`Filter by ${tag.name}`}
        />
        <span className="text-[0.65rem] font-medium uppercase leading-none tracking-wide text-ink-muted">
          Filter
        </span>
      </label>

      <div className="min-w-0 flex-1">
        <Link
          to={`/tags/${tag.id}/pictures`}
          className="block truncate text-base font-semibold leading-snug text-accent underline-offset-2 hover:underline focus-visible:rounded focus-visible:ring-2 focus-visible:ring-accent/40"
          title={`Open ${tag.name} details`}
        >
          {tag.name}
        </Link>
        <p className="mt-0.5 truncate text-xs leading-snug text-ink-muted">
          {photoLabel}
          <span className="mx-1 opacity-40">·</span>
          {childLabel}
        </p>
      </div>
    </div>
  )
}
