import { useEffect, useMemo, useState } from 'react'
import { fetchTags } from '../api/client'
import type { Tag } from '../api/types'
import { TagCard } from '../components/TagCard'

function isYearMeta(tag: Tag): boolean {
  return tag.source === 'metadata'
}

function sortYearsDesc(a: Tag, b: Tag): number {
  return b.name.localeCompare(a.name, undefined, { numeric: true })
}

function sortNameAsc(a: Tag, b: Tag): number {
  return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
}

export function LibraryPage() {
  const [tags, setTags] = useState<Tag[] | null>(null)
  const [error, setError] = useState<string | null>(null)

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
    return {
      yearTags: list.filter(isYearMeta).sort(sortYearsDesc),
      otherTags: list.filter((t) => !isYearMeta(t)).sort(sortNameAsc),
    }
  }, [tags])

  return (
    <div className="w-full px-8 py-6">
      <div className="mb-5">
        <h1 className="text-2xl font-semibold text-ink">Library</h1>
        <p className="mt-1 text-base text-ink-muted">
          Browse tags in your catalog
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-label-orange/40 bg-surface px-3 py-2 text-base text-ink">
          <span className="font-medium text-label-orange">Couldn’t load tags.</span>{' '}
          <span className="text-ink-muted">
            Is FastAPI running on port 8765 with <code className="text-ink">GET /api/tags</code>?
          </span>
          <div className="mt-1 font-mono text-sm text-ink-muted">{error}</div>
        </div>
      )}

      {tags === null && !error && (
        <p className="text-base text-ink-muted">Loading tags…</p>
      )}

      {tags && tags.length === 0 && (
        <p className="rounded-md border border-line bg-surface px-3 py-4 text-base text-ink-muted">
          No tags yet — scan photos to build your library.
        </p>
      )}

      {tags && tags.length > 0 && (
        <div className="space-y-7">
          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-muted">
              Years
            </h2>
            {yearTags.length === 0 ? (
              <p className="text-base text-ink-muted">No year tags yet.</p>
            ) : (
              <div className="grid grid-cols-3 gap-4 xl:grid-cols-4 2xl:grid-cols-5">
                {yearTags.map((tag) => (
                  <TagCard key={tag.id} tag={tag} />
                ))}
              </div>
            )}
          </section>

          <div className="border-t border-line" role="separator" />

          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-muted">
              Tags
            </h2>
            {otherTags.length === 0 ? (
              <p className="text-base text-ink-muted">No vision tags yet.</p>
            ) : (
              <div className="grid grid-cols-3 gap-4 xl:grid-cols-4 2xl:grid-cols-5">
                {otherTags.map((tag) => (
                  <TagCard key={tag.id} tag={tag} />
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
