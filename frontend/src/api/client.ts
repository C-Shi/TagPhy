import type { Picture, TagResponse, TagPictureResponse } from './types'

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
export async function fetchTags(): Promise<TagResponse[]> {
  const res = await fetch('/api/tags')
  const data = await parseJson<TagResponse[]>(res)
  return data || []
}

export async function fetchTagPictures(id: number): Promise<TagPictureResponse> {
  const res = await fetch(`/api/tags/${id}/pictures`)
  return parseJson<TagPictureResponse>(res)
}

export type FetchPicturesParams = {
  pagination?: number
  tagIds?: number[]
}

export async function fetchPictures(
  params: FetchPicturesParams = {},
): Promise<Picture[]> {
  const { pagination = 1, tagIds = [] } = params
  const search = new URLSearchParams()
  search.set('pagination', String(pagination))
  for (const id of tagIds) {
    search.append('tag_ids', String(id))
  }
  const res = await fetch(`/api/pictures?${search.toString()}`)
  const data = await parseJson<Picture[]>(res)
  return data || []
}
