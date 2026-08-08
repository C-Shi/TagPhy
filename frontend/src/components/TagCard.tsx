import { Link } from 'react-router-dom'
import type { Tag } from '../api/types'

type Props = {
  tag: Tag
}

export function TagCard({ tag }: Props) {
  return (
    <Link
      to={`/tags/${tag.id}/pictures`}
      className="block rounded-md border border-line bg-surface p-4 outline-none transition-colors hover:border-accent/40 hover:bg-accent-soft/40 focus-visible:ring-2 focus-visible:ring-accent/40"
    >
      <div className="truncate text-lg font-semibold text-ink">
        {tag.name}
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        <span className="rounded px-2 py-0.5 text-sm font-medium text-label-blue ring-1 ring-label-blue/25">
          {tag.photo_count} {tag.photo_count === 1 ? 'photo' : 'photos'}
        </span>
        <span className="rounded px-2 py-0.5 text-sm font-medium text-label-pink ring-1 ring-label-pink/25">
          {tag.child_count}{' '}
          {tag.child_count === 1 ? 'child tag' : 'child tags'}
        </span>
      </div>
    </Link>
  )
}
