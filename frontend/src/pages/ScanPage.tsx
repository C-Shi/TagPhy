import { useEffect, useRef, useState } from "react";
import {
  connectScanLog,
  startScan,
  stopScan,
  getScanStatus,
} from "../api/scan";
import type { ScanJobStatus, ScanLog } from "../api/types";
import { BrowseModal } from "../components/BrowseModal";
import { ConfirmModal } from "../components/ConfirmModal";
import { ScanLogPanel } from "../components/ScanLog";
import { useScanLock } from "../components/ScanLockContext";

function isBusy(status: ScanJobStatus) {
  return status === "running" || status === "stopping";
}

export function ScanPage() {
  const { setScanLocked } = useScanLock();
  const [path, setPath] = useState("");
  const [jobStatus, setJobStatus] = useState<ScanJobStatus>("idle");
  const [logs, setLogs] = useState<ScanLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [browseOpen, setBrowseOpen] = useState(false);
  const [scanConfirmOpen, setScanConfirmOpen] = useState(false);
  const [stopConfirmOpen, setStopConfirmOpen] = useState(false);
  const jobStatusRef = useRef(jobStatus);
  const checkStatusIntervalRef = useRef<number | null>(null);
  jobStatusRef.current = jobStatus;

  useEffect(() => {
    setScanLocked(isBusy(jobStatus));
  }, [jobStatus, setScanLocked]);

  useEffect(() => {
    return () => setScanLocked(false);
  }, [setScanLocked]);

  useEffect(() => {
    const unsubscribe = connectScanLog((log) => {
      setLogs((prev) => [...prev, log]);
      const status = (log.status || "").toLowerCase();
      if (status === "complete" || status === "summary" || status === "idle") {
        if (jobStatusRef.current !== "idle") {
          setPath("");
          setJobStatus("idle");
        }
      }
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    return () => {
      if (checkStatusIntervalRef.current) {
        clearInterval(checkStatusIntervalRef.current);
        checkStatusIntervalRef.current = null;
      }
    };
  }, []);

  async function onConfirmScan() {
    if (!path || isBusy(jobStatus)) return;
    setScanConfirmOpen(false);
    setError(null);
    setLogs([]);
    try {
      const { status } = await startScan(path);
      setJobStatus(status);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to start scan");
    }
  }

  async function onConfirmStop() {
    setStopConfirmOpen(false);
    setError(null);
    try {
      const { status } = await stopScan();
      setJobStatus(status as ScanJobStatus);

      checkStatusIntervalRef.current = setInterval(async () => {
        const { status } = await getScanStatus();
        setJobStatus(status as ScanJobStatus);

        if (status === "idle") {
          clearInterval(checkStatusIntervalRef.current!);
          checkStatusIntervalRef.current = null;
        }
      }, 1000);
      setPath("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to stop scan");
    }
  }

  const busy = isBusy(jobStatus);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="shrink-0 border-b border-line bg-panel px-4 py-4 library:px-6">
        <h1 className="text-2xl font-semibold text-ink">Scan</h1>
        <p className="mt-1 text-base text-ink-muted">
          Choose a file or folder, then scan. Processed files stay if you stop.
        </p>
      </div>

      <div className="flex min-h-0 flex-1 flex-col px-4 py-6 library:px-6">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              readOnly
              value={path}
              placeholder="No path selected"
              className="min-w-0 flex-1 rounded-md border border-line bg-surface px-3 py-1.5 font-mono text-base text-ink placeholder:text-ink-muted"
            />
            <button
              type="button"
              disabled={busy}
              onClick={() => setBrowseOpen(true)}
              className="rounded bg-accent px-3 py-1.5 text-base font-medium text-on-accent hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Browse
            </button>
            {busy ? (
              <button
                type="button"
                disabled={jobStatus === "stopping"}
                onClick={() => setStopConfirmOpen(true)}
                className="rounded bg-label-orange px-3 py-1.5 text-base font-semibold text-on-chip hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {jobStatus === "stopping" ? "Stopping…" : "Stop"}
              </button>
            ) : (
              <button
                type="button"
                disabled={!path}
                onClick={() => setScanConfirmOpen(true)}
                className="rounded bg-accent px-3 py-1.5 text-base font-medium text-on-accent hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Scan
              </button>
            )}
          </div>

          {error && (
            <div className="rounded-md border border-label-orange/40 bg-surface px-3 py-2 text-base">
              <span className="font-medium text-label-orange">{error}</span>
            </div>
          )}

          <ScanLogPanel logs={logs} />
        </div>
      </div>

      {browseOpen && (
        <BrowseModal
          onClose={() => setBrowseOpen(false)}
          onSelect={(selected) => {
            setPath(selected);
            setBrowseOpen(false);
          }}
        />
      )}

      {scanConfirmOpen && (
        <ConfirmModal
          title="Files will be moved"
          message={`Scanning permanently moves each successful file into Photo_Tagged/<year>/ (or Photo_Tagged/Unknown/). The original is not left in place. Stopping a scan does not undo files already moved.\n\n${path}`}
          confirmLabel="Start scan"
          onCancel={() => setScanConfirmOpen(false)}
          onConfirm={onConfirmScan}
        />
      )}

      {stopConfirmOpen && (
        <ConfirmModal
          title="Stop this scan?"
          message="Files already processed stay where they are. The current image will finish, then the scan stops."
          confirmLabel="Stop scan"
          onCancel={() => setStopConfirmOpen(false)}
          onConfirm={onConfirmStop}
        />
      )}
    </div>
  );
}
