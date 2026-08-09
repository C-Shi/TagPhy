import { useEffect, useMemo, useState } from 'react'
import { fetchTags } from '../api/client'
import type { TagResponse } from '../api/types'
import { TagCard } from '../components/TagCard'

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

export function LibraryPage() {
  const [tags, setTags] = useState<TagResponse[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedTagIds, setSelectedTagIds] = useState<Set<number>>(
    () => new Set(),
  )
  const [tagSort, setTagSort] = useState<TagSort>('name')

  useEffect(() => {
    let cancelled = false
    setError(null)
    fetchTags()
      .then((data) => {
        if (!cancelled) setTags(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setTags(null)
          setError(err instanceof Error ? err.message : 'Failed to load tags')
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  const { yearTags, otherTags } = useMemo(() => {
    const list = tags ?? []
    const vision = list.filter((t) => !isYearMeta(t))
    return {
      yearTags: list.filter(isYearMeta).sort(sortYearsDesc),
      otherTags: vision.sort(
        tagSort === 'photos' ? sortPhotosDesc : sortNameAsc,
      ),
    }
  }, [tags, tagSort])

  const selectedTags = useMemo(() => {
    if (!tags) return []
    return tags.filter((t) => selectedTagIds.has(t.id))
  }, [tags, selectedTagIds])

  function toggleSelect(tagId: number) {
    setSelectedTagIds((prev) => {
      const next = new Set(prev)
      if (next.has(tagId)) next.delete(tagId)
      else next.add(tagId)
      return next
    })
  }

  function clearFilters() {
    setSelectedTagIds(new Set())
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="shrink-0 border-b border-line bg-panel px-4 py-4 library:px-6">
        <h1 className="text-2xl font-semibold text-ink">Library</h1>
        <p className="mt-1 text-base text-ink-muted">
          Use Filter to AND tags for preview. Click a tag name to open its page.
        </p>

        {/* Always reserve one filter-row so selecting tags does not shift layout */}
        <div
          className="mt-3 flex min-h-9 min-w-0 flex-wrap items-center gap-2"
          aria-live="polite"
        >
          {selectedTags.length > 0 && (
            <>
              <span className="text-sm font-medium text-ink-muted">Filters:</span>
              {selectedTags.map((tag) => (
                <span
                  key={tag.id}
                  className="rounded bg-accent px-2 py-0.5 text-sm font-medium text-on-accent"
                >
                  {tag.name}
                </span>
              ))}
              <button
                type="button"
                onClick={clearFilters}
                className="rounded bg-label-orange px-2.5 py-1 text-sm font-semibold text-on-chip hover:brightness-110"
              >
                Clear filters
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mx-4 mt-4 rounded-md border border-label-orange/40 bg-surface px-3 py-2 text-base text-ink library:mx-6">
          <span className="font-medium text-label-orange">
            Couldn’t load tags.
          </span>{' '}
          <span className="text-ink-muted">
            Is FastAPI running on port 8765 with{' '}
            <code className="text-ink">GET /api/tags</code>?
          </span>
          <div className="mt-1 font-mono text-sm text-ink-muted">{error}</div>
        </div>
      )}

      {tags === null && !error && (
        <p className="px-4 py-4 text-base text-ink-muted library:px-6">
          Loading tags…
        </p>
      )}

      {tags && tags.length === 0 && (
        <p className="m-4 rounded-md border border-line bg-surface px-3 py-4 text-base text-ink-muted library:m-6">
          No tags yet — scan photos to build your library.
        </p>
      )}

      {tags && tags.length > 0 && (
        <div className="flex min-h-0 min-w-0 flex-1 flex-col library:flex-row">
          {/* Left: narrow single-column tags */}
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
                      <TagCard
                        key={tag.id}
                        tag={tag}
                        selected={selectedTagIds.has(tag.id)}
                        onToggleSelect={toggleSelect}
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
                      <TagCard
                        key={tag.id}
                        tag={tag}
                        selected={selectedTagIds.has(tag.id)}
                        onToggleSelect={toggleSelect}
                      />
                    ))}
                  </div>
                )}
              </section>
            </div>
          </div>

          {/* Right: majority preview */}
          <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-auto bg-canvas/40 px-4 py-4 library:px-6">
            <h2 className="text-lg font-semibold text-ink">Preview</h2>
            <p className="mt-1 text-sm text-ink-muted">
              {selectedTags.length === 0
                ? 'Photos ordered by newest will appear here.'
                : `Will show photos matching all of: ${selectedTags.map((t) => t.name).join(' + ')} (AND).`}
            </p>
            <div className="mt-6 flex flex-1 flex-col items-center justify-center rounded-md border border-dashed border-line bg-surface px-4 py-12 text-center">
              <p className="text-base font-semibold text-ink">Photo preview</p>
              <p className="mt-1 text-sm text-ink-muted">Coming soon</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
