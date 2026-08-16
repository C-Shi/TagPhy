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

export class TagResponse {
  id!: number
  name!: string
  source!: "vision" | "metadata"
  photo_count!: number
  children!: TagRef[]
  parents!: TagRef[]
}

export type TagPictureResponse = {
  id: number
  name: string
  source: "vision" | "metadata"
  children: TagRef[]
  parents: TagRef[]
  pictures: Picture[]
}

/** Row from GET /api/pictures (images table). */
export type Picture = {
  id: number
  file_name: string
  file_path: string
  year: string
  location: string
  description: string
  created_at: string
  updated_at: string
}

/** idle | running | stopping — matches ScanJobController. */
export type ScanJobStatus = "idle" | "running" | "stopping"

/**
 * Line from WS /ws/scan_log (backend ScanLog).
 * FE colors: fail = orange, warn = yellow, info = muted, summary = accent.
 */
export type ScanLogLevel = "info" | "warn" | "fail" | "summary"

export type ScanLog = {
  status: string
  stage: string
  msg: string
}

/** GET /api/scan/browse?path= (backend not built yet). */
export type BrowseEntry = {
  name: string
  type: "dir" | "file"
  path: string
}

export type BrowseResponse = {
  current: string
  parent: string | null
  entries: BrowseEntry[]
  is_under_root: boolean
}
