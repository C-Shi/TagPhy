import type { BrowseResponse, ScanLog, ScanStatusResponse } from "./types"

async function parseScanStatusResponse(response: Response): Promise<ScanStatusResponse> {
  const body = (await response.json()) as ScanStatusResponse & { detail?: string }
  if (!response.ok) {
    throw new Error(body.message || body.detail || "Scan request failed")
  }
  return body
}

/**
 * POST /api/scan
 * body: { path: string }
 * success/error body: { status: "idle"|"running"|"stopping", message?: string }
 */
export async function startScan(path: string): Promise<ScanStatusResponse> {
  const response = await fetch("/api/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  })
  return parseScanStatusResponse(response)
}

/**
 * POST /api/scan_stop
 * success body: { status: "idle"|"stopping" }
 */
export async function stopScan(): Promise<ScanStatusResponse> {
  const response = await fetch("/api/scan_stop", { method: "POST" })
  return parseScanStatusResponse(response)
}

/**
 * GET /api/scan/status
 * success body: { status: "idle"|"running"|"stopping" }
 */
export async function getScanStatus(): Promise<ScanStatusResponse> {
  const response = await fetch("/api/scan/status")
  return parseScanStatusResponse(response)
}

/**
 * GET /api/scan/browse?path=
 * Hide Photo_Tagged on the backend; FE renders whatever is returned.
 */
export async function fetchBrowse(path: string): Promise<BrowseResponse> {
  const search = new URLSearchParams()
  search.set("path", path)
  const res = await fetch(`/api/scan/browse?${search.toString()}`)
  if (!res.ok) {
    const body = await res.text().catch(() => "")
    throw new Error(
      body
        ? `API ${res.status}: ${body}`
        : `API request failed (${res.status} ${res.statusText})`,
    )
  }
  return res.json() as Promise<BrowseResponse>
}

/**
 * WS /ws/scan_log — open on Scan page mount, stay until unmount.
 * Returns an unsubscribe function.
 */
export function connectScanLog(
  onMessage: (log: ScanLog) => void,
  _onClose?: () => void,
): () => void {
  const ws = new WebSocket("/ws/scan_log")
  ws.onmessage = (ev) => {
    try {
      const log = JSON.parse(ev.data)
      onMessage(log)
    } catch (error) {
      console.error("Failed to parse scan log", error)
    }
  }
  return () => {
    ws.close()
  }
}
