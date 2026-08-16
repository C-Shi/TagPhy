import { useEffect, useState } from "react"
import { fetchBrowse } from "../api/scan"
import type { BrowseEntry, BrowseResponse } from "../api/types"

type BrowseModalProps = {
  onClose: () => void
  onSelect: (path: string) => void
}

export function BrowseModal({ onClose, onSelect }: BrowseModalProps) {
  const [browse, setBrowse] = useState<BrowseResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  function load(path: string) {
    setError(null)
    fetchBrowse(path)
      .then(setBrowse)
      .catch((err: unknown) => {
        setBrowse(null)
        setError(err instanceof Error ? err.message : "Failed to browse")
      })
  }

  useEffect(() => {
    load("")
  }, [])

  function onEntry(entry: BrowseEntry) {
    if (entry.type === "dir") {
      load(entry.path)
      return
    }
    onSelect(entry.path)
  }

  return (
    <div
      className="fixed inset-0 z-20 flex items-center justify-center bg-header/50 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="browse-title"
    >
      <div className="flex max-h-[80vh] w-full max-w-lg flex-col rounded-md border border-line bg-surface">
        <div className="border-b border-line px-4 py-3">
          <h2 id="browse-title" className="text-lg font-semibold text-ink">
            Select a file or folder
          </h2>
          <p className="mt-1 truncate font-mono text-sm text-ink-muted">
            {browse?.current || "/"}
          </p>
        </div>

        <div className="min-h-0 flex-1 overflow-auto px-2 py-2">
          {error && (
            <div className="mx-2 rounded-md border border-label-orange/40 px-3 py-2 text-sm text-label-orange">
              {error}
            </div>
          )}
          {!error && !browse && (
            <p className="px-3 py-2 text-base text-ink-muted">Loading…</p>
          )}
          {browse && (
            <ul>
              {browse.parent !== null && (
                <li>
                  <button
                    type="button"
                    onClick={() => load(browse.parent as string)}
                    className="w-full rounded px-3 py-2 text-left text-base text-ink hover:bg-accent-soft"
                  >
                    ↑ Parent folder
                  </button>
                </li>
              )}
              {browse.entries.length === 0 && (
                <li className="px-3 py-4 text-base text-ink-muted">
                  No files or folders here.
                </li>
              )}
              {browse.entries.map((entry) => (
                <li key={entry.path}>
                  <button
                    type="button"
                    onClick={() => onEntry(entry)}
                    className="w-full rounded px-3 py-2 text-left text-base text-ink hover:bg-accent-soft"
                  >
                    <span className="text-ink-muted">
                      {entry.type === "dir" ? "Folder — " : ""}
                    </span>
                    {entry.name}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t border-line px-4 py-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded bg-label-orange px-3 py-1.5 text-base font-semibold text-on-chip hover:brightness-110"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!browse}
            onClick={() => browse && onSelect(browse.current)}
            className="rounded bg-accent px-3 py-1.5 text-base font-medium text-on-accent hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Select this folder
          </button>
        </div>
      </div>
    </div>
  )
}
