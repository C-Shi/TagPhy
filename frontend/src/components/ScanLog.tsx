import type { ScanLog, ScanLogLevel } from "../api/types"

function logLevel(log: ScanLog): ScanLogLevel {
  const status = (log.status || "").toLowerCase()
  if (status === "fail" || status === "error") return "fail"
  if (status === "warn" || status === "skip" || status === "warning") return "warn"
  if (status === "complete" || status === "summary" || status === "success")
    return "summary"
  return "info"
}

const levelClass: Record<ScanLogLevel, string> = {
  fail: "text-label-orange",
  warn: "text-label-yellow",
  summary: "text-accent",
  info: "text-ink-muted",
}

type ScanLogPanelProps = {
  logs: ScanLog[]
}

export function ScanLogPanel({ logs }: ScanLogPanelProps) {
  return (
    <section
      className="flex min-h-48 flex-1 flex-col overflow-hidden rounded-md border border-line bg-surface"
      aria-live="polite"
    >
      <div className="border-b border-line px-3 py-2 text-sm font-medium text-ink-muted">
        Log
      </div>
      <div className="min-h-0 flex-1 overflow-auto px-3 py-3 font-mono text-sm">
        {logs.length === 0 ? (
          <p className="text-ink-muted">
            Idle — log appears when a scan runs.
          </p>
        ) : (
          <ul className="space-y-1">
            {logs.map((log, i) => (
              <li key={`${i}-${log.msg}`} className={levelClass[logLevel(log)]}>
                {log.msg}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
