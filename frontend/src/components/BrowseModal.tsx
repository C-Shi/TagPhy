import { useEffect, useMemo, useState } from "react"
import { fetchBrowse } from "../api/scan"
import type { BrowseEntry, BrowseResponse } from "../api/types"

type BrowseModalProps = {
  onClose: () => void
  onSelect: (path: string) => void
}

function pathCrumbs(current: string): { label: string; path: string }[] {
  const parts = current.split("/").filter(Boolean)
  const crumbs: { label: string; path: string }[] = []
  let acc = current.startsWith("/") ? "" : ""
  for (const part of parts) {
    acc += `/${part}`
    crumbs.push({ label: part, path: acc })
  }
  return crumbs
}

function sortEntries(entries: BrowseEntry[]): BrowseEntry[] {
  return [...entries].sort((a, b) => {
    if (a.type !== b.type) return a.type === "dir" ? -1 : 1
    return a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
  })
}

export function BrowseModal({ onClose, onSelect }: BrowseModalProps) {
  const [browse, setBrowse] = useState<BrowseResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<BrowseEntry | null>(null)

  function load(path: string) {
    setError(null)
    setSelected(null)
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

  const entries = useMemo(
    () => (browse ? sortEntries(browse.entries) : []),
    [browse],
  )
  const crumbs = browse ? pathCrumbs(browse.current) : []

  function onEntryClick(entry: BrowseEntry) {
    setSelected(entry)
  }

  function onEntryOpen(entry: BrowseEntry) {
    if (entry.type === "dir") {
      load(entry.path)
      return
    }
    onSelect(entry.path)
  }

  function onOpen() {
    if (!browse) return
    if (selected?.type === "file") {
      onSelect(selected.path)
      return
    }
    if (selected?.type === "dir") {
      load(selected.path)
      return
    }
    onSelect(browse.current)
  }

  const openLabel =
    selected?.type === "file"
      ? "Open"
      : selected?.type === "dir"
        ? "Open"
        : "Select this folder"

  return (
    <div
      className="fixed inset-0 z-20 flex items-center justify-center bg-header/50 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="browse-title"
    >
      <div className="flex max-h-[min(32rem,80vh)] w-full max-w-2xl flex-col overflow-hidden rounded-md border border-line bg-surface shadow-lg">
        <div className="flex items-center justify-between border-b border-line px-3 py-2">
          <h2 id="browse-title" className="text-base font-semibold text-ink">
            Open
          </h2>
        </div>

        <div className="flex items-center gap-2 border-b border-line bg-panel px-2 py-2">
          <button
            type="button"
            disabled={!browse || browse.parent === null}
            onClick={() => browse?.parent !== null && load(browse.parent)}
            className="inline-flex h-8 w-8 items-center justify-center rounded border border-line bg-surface text-ink disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Back"
            title="Back"
          >
            <i className="fa-solid fa-chevron-left text-sm" aria-hidden />
          </button>
          <nav
            className="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto text-sm"
            aria-label="Path"
          >
            {crumbs.map((crumb, i) => (
              <span key={crumb.path} className="flex shrink-0 items-center gap-1">
                {i > 0 && (
                  <i
                    className="fa-solid fa-chevron-right text-[0.65rem] text-ink-muted"
                    aria-hidden
                  />
                )}
                <button
                  type="button"
                  onClick={() => load(crumb.path)}
                  className="max-w-[10rem] truncate rounded px-1.5 py-0.5 text-ink hover:bg-accent-soft"
                >
                  {crumb.label}
                </button>
              </span>
            ))}
          </nav>
        </div>

        <div className="min-h-0 flex-1 overflow-auto bg-surface">
          {error && (
            <div className="m-3 rounded-md border border-label-orange/40 px-3 py-2 text-sm text-label-orange">
              {error}
            </div>
          )}
          {!error && !browse && (
            <p className="px-4 py-6 text-base text-ink-muted">Loading…</p>
          )}
          {browse && entries.length === 0 && (
            <p className="px-4 py-6 text-base text-ink-muted">
              This folder is empty.
            </p>
          )}
          {browse && entries.length > 0 && (
            <table className="w-full text-left text-base">
              <thead className="sticky top-0 bg-panel text-sm font-medium text-ink-muted">
                <tr className="border-b border-line">
                  <th className="px-3 py-1.5 font-medium">Name</th>
                  <th className="w-28 px-3 py-1.5 font-medium">Kind</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => {
                  const isSelected = selected?.path === entry.path
                  return (
                    <tr
                      key={entry.path}
                      className={
                        isSelected
                          ? "bg-accent text-on-accent"
                          : "text-ink hover:bg-accent-soft"
                      }
                    >
                      <td className="px-3 py-1.5">
                        <button
                          type="button"
                          className="flex w-full items-center gap-2.5 text-left"
                          onClick={() => onEntryClick(entry)}
                          onDoubleClick={() => onEntryOpen(entry)}
                        >
                          <i
                            className={
                              entry.type === "dir"
                                ? "fa-solid fa-folder w-4 shrink-0 text-label-yellow"
                                : "fa-solid fa-file-image w-4 shrink-0 text-label-blue"
                            }
                            style={isSelected ? { color: "inherit" } : undefined}
                            aria-hidden
                          />
                          <span className="truncate">{entry.name}</span>
                        </button>
                      </td>
                      <td
                        className={`px-3 py-1.5 text-sm ${isSelected ? "text-on-accent" : "text-ink-muted"}`}
                      >
                        {entry.type === "dir" ? "Folder" : "Image"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-line bg-panel px-3 py-2.5">
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-line bg-surface px-3 py-1.5 text-base font-medium text-ink hover:bg-accent-soft"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!browse}
            onClick={onOpen}
            className="rounded bg-accent px-3 py-1.5 text-base font-medium text-on-accent hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {openLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
