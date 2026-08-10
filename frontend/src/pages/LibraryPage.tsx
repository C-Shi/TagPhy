import { useEffect, useMemo, useState } from 'react'
import { fetchPictures, fetchTags } from '../api/client'
import type { Picture, TagResponse } from '../api/types'
import { Preview } from '../components/Preview'
import { TagList } from '../components/TagList'

export function LibraryPage() {
  const [tags, setTags] = useState<TagResponse[] | null>(null)
  const [pictures, setPictures] = useState<Picture[]>([])
  const [error, setError] = useState<string | null>(null)
  const [picturesError, setPicturesError] = useState<string | null>(null)
  const [selectedTagIds, setSelectedTagIds] = useState<Set<number>>(
    () => new Set(),
  )

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

  useEffect(() => {
    let cancelled = false
    setPicturesError(null)
    fetchPictures({
      pagination: 1,
      tagIds: [...selectedTagIds],
    })
      .then((data) => {
        if (!cancelled) setPictures(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setPictures([])
          setPicturesError(
            err instanceof Error ? err.message : 'Failed to load pictures',
          )
        }
      })
    return () => {
      cancelled = true
    }
  }, [selectedTagIds])

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

      {picturesError && (
        <div className="mx-4 mt-4 rounded-md border border-label-orange/40 bg-surface px-3 py-2 text-base text-ink library:mx-6">
          <span className="font-medium text-label-orange">
            Couldn’t load pictures.
          </span>
          <div className="mt-1 font-mono text-sm text-ink-muted">
            {picturesError}
          </div>
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
          <TagList
            tags={tags}
            selectedTagIds={selectedTagIds}
            onToggleSelect={toggleSelect}
          />
          <Preview pictures={pictures} />
        </div>
      )}
    </div>
  )
}
