import type { BrowseResponse, ScanLog } from "./types"

/**
 * POST /api/scan
 * body: { path: string }
 */
export async function startScan(_path: string): Promise<void> {
  // TODO: fetch('/api/scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) })
}

/**
 * POST /api/scan_stop
 */
export async function stopScan(): Promise<void> {
  // TODO: fetch('/api/scan_stop', { method: 'POST' })
}

/**
 * GET /api/scan/browse?path=
 * Hide Photo_Tagged on the backend; FE renders whatever is returned.
 */
export async function fetchBrowse(path: string): Promise<BrowseResponse> {
  // TODO: fetch(`/api/scan/browse?path=${encodeURIComponent(path)}`)
  return { current: path, parent: null, entries: [] }
}

/**
 * WS /ws/scan_log — open on Scan page mount, stay until unmount.
 * Returns an unsubscribe function.
 */
export function connectScanLog(
  _onMessage: (log: ScanLog) => void,
  _onClose?: () => void,
): () => void {
  // TODO: const ws = new WebSocket(...)
  // TODO: ws.onmessage = (ev) => onMessage(JSON.parse(ev.data))
  // TODO: return () => ws.close()
  return () => {}
}
