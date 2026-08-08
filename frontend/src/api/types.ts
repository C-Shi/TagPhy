/**
 * API contract for FastAPI (implement on the backend).
 *
 * GET /api/tags
 *   → { tags: Tag[] }
 *
 * GET /api/tags/:id
 *   → Tag  (404 if missing)
 *
 * Grouping rules (frontend):
 *   - source === "metadata" → Year sector (sort name desc as year)
 *   - everything else → Tags sector (sort name A–Z)
 *
 * Counts:
 *   - photo_count: direct image_tags only
 *   - child_count: one-hop tag_edges where this tag is parent
 */

export type TagRef = {
  id: number
  name: string
}

export type Tag = {
  id: number
  name: string
  source: string
  description: string
  photo_count: number
  child_count: number
  parents: TagRef[]
  children: TagRef[]
}

export type TagsResponse = {
  tags: Tag[]
}
