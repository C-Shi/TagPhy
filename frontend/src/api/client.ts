import type { Tag, TagsResponse } from './types'

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(
      body
        ? `API ${res.status}: ${body}`
        : `API request failed (${res.status} ${res.statusText})`,
    )
  }
  return res.json() as Promise<T>
}

/** Relative /api — Vite proxies in dev; same-origin when packaged. */
export async function fetchTags(): Promise<Tag[]> {
  const res = await fetch('/api/tags')
  const data = await parseJson<TagsResponse>(res)
  return data.tags ?? []
}

export async function fetchTag(id: number): Promise<Tag> {
  const res = await fetch(`/api/tags/${id}`)
  return parseJson<Tag>(res)
}
