import { useMemo, useState } from 'react'
import type { TagResponse } from '../api/types'
import { TagListItem } from './TagListItem'

function isYearMeta(tag: TagResponse): boolean {
  return tag.source === 'metadata'
}

function sortYearsDesc(a: TagResponse, b: TagResponse): number {
  return b.name.localeCompare(a.name, undefined, { numeric: true })
}

function sortNameAsc(a: TagResponse, b: TagResponse): number {
  return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
}

function sortPhotosDesc(a: TagResponse, b: TagResponse): number {
  const byCount = b.photo_count - a.photo_count
  return byCount !== 0 ? byCount : sortNameAsc(a, b)
}

type TagSort = 'name' | 'photos'

type Props = {
  tags: TagResponse[]
  selectedTagIds: Set<number>
  onToggleSelect: (tagId: number) => void
}

export function TagList({ tags, selectedTagIds, onToggleSelect }: Props) {
  const [tagSort, setTagSort] = useState<TagSort>('name')

  const { yearTags, otherTags } = useMemo(() => {
    const vision = tags.filter((t) => !isYearMeta(t))
    return {
      yearTags: tags.filter(isYearMeta).sort(sortYearsDesc),
      otherTags: vision.sort(
        tagSort === 'photos' ? sortPhotosDesc : sortNameAsc,
      ),
    }
  }, [tags, tagSort])

  return (
    <div className="min-h-0 min-w-0 overflow-auto border-b border-line px-3 py-3 library:w-56 library:shrink-0 library:border-b-0 library:border-r library:px-3">
      <div className="space-y-4">
        <section>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink-muted">
            Years
          </h2>
          {yearTags.length === 0 ? (
            <p className="text-sm text-ink-muted">No year tags yet.</p>
          ) : (
            <div className="flex flex-col gap-1.5">
              {yearTags.map((tag) => (
                <TagListItem
                  key={tag.id}
                  tag={tag}
                  selected={selectedTagIds.has(tag.id)}
                  onToggleSelect={onToggleSelect}
                />
              ))}
            </div>
          )}
        </section>

        <div className="border-t border-line" role="separator" />

        <section>
          <div className="mb-2 flex items-center justify-between gap-1">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted">
              Tags
            </h2>
            <div
              className="inline-flex rounded border border-line bg-surface p-0.5"
              role="group"
              aria-label="Sort tags"
            >
              <button
                type="button"
                onClick={() => setTagSort('name')}
                className={[
                  'rounded px-1.5 py-0.5 text-xs font-semibold',
                  tagSort === 'name'
                    ? 'bg-accent text-on-accent'
                    : 'text-ink-muted hover:text-ink',
                ].join(' ')}
              >
                Name
              </button>
              <button
                type="button"
                onClick={() => setTagSort('photos')}
                className={[
                  'rounded px-1.5 py-0.5 text-xs font-semibold',
                  tagSort === 'photos'
                    ? 'bg-accent text-on-accent'
                    : 'text-ink-muted hover:text-ink',
                ].join(' ')}
              >
                Photos
              </button>
            </div>
          </div>
          {otherTags.length === 0 ? (
            <p className="text-sm text-ink-muted">No vision tags yet.</p>
          ) : (
            <div className="flex flex-col gap-1.5">
              {otherTags.map((tag) => (
                <TagListItem
                  key={tag.id}
                  tag={tag}
                  selected={selectedTagIds.has(tag.id)}
                  onToggleSelect={onToggleSelect}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
