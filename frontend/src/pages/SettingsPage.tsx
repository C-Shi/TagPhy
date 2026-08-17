import { useEffect, useState } from "react";
import { fetchSettings, updateSetting } from "../api/client";
import { useScanLock } from "../components/ScanLockContext";

type SettingsSection = "privacy" | "about";

const SECTIONS: { id: SettingsSection; label: string; hint: string }[] = [
  { id: "privacy", label: "Privacy", hint: "Scan screening" },
  { id: "about", label: "About", hint: "This copy of TagPhy" },
];

function Switch({
  checked,
  disabled,
  onChange,
  label,
}: {
  checked: boolean;
  disabled: boolean;
  onChange: (next: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={[
        "relative h-7 w-12 shrink-0 rounded-full transition-colors",
        checked ? "bg-accent" : "bg-line",
        disabled
          ? "cursor-not-allowed opacity-50"
          : "hover:brightness-110",
      ].join(" ")}
    >
      <span
        className={[
          "absolute top-0.5 h-6 w-6 rounded-full bg-on-accent shadow transition-transform",
          checked ? "left-5" : "left-0.5",
        ].join(" ")}
      />
    </button>
  );
}

export function SettingsPage() {
  const { scanLocked } = useScanLock();
  const [section, setSection] = useState<SettingsSection>("privacy");
  const [enabled, setEnabled] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    fetchSettings()
      .then((data) => {
        if (!cancelled) {
          setEnabled(data.privacy_pre_check !== "false");
          setLoaded(true);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load settings",
          );
          setLoaded(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onToggle(next: boolean) {
    if (scanLocked || saving || !loaded) return;
    setSaving(true);
    setError(null);
    const previous = enabled;
    setEnabled(next);
    try {
      const data = await updateSetting(
        "privacy_pre_check",
        next ? "true" : "false",
      );
      setEnabled(data.privacy_pre_check !== "false");
      setSavedFlash(true);
      window.setTimeout(() => setSavedFlash(false), 1600);
    } catch (err: unknown) {
      setEnabled(previous);
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  const toggleDisabled = !loaded || scanLocked || saving;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="shrink-0 border-b border-line bg-panel px-4 py-4 library:px-6">
        <h1 className="text-2xl font-semibold text-ink">Settings</h1>
        <p className="mt-1 text-base text-ink-muted">
          Preferences for this TagPhy copy. Saved on the drive, not in the
          cloud.
        </p>
      </div>

      <div className="flex min-h-0 flex-1 flex-col library:flex-row">
        <nav
          className="shrink-0 border-b border-line bg-panel px-3 py-3 library:w-56 library:border-b-0 library:border-r library:px-4 library:py-5"
          aria-label="Settings sections"
        >
          <ul className="flex gap-1 library:flex-col">
            {SECTIONS.map((item) => {
              const active = section === item.id;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => setSection(item.id)}
                    className={[
                      "w-full rounded-md px-3 py-2 text-left",
                      active
                        ? "bg-accent-soft text-ink"
                        : "text-ink-muted hover:bg-surface hover:text-ink",
                    ].join(" ")}
                  >
                    <span className="block text-base font-medium">
                      {item.label}
                    </span>
                    <span className="mt-0.5 hidden text-sm library:block">
                      {item.hint}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="min-h-0 flex-1 overflow-auto px-4 py-6 library:px-8">
          <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
            {error && (
              <div className="rounded-md border border-label-orange/40 bg-surface px-3 py-2 text-base">
                <span className="font-medium text-label-orange">{error}</span>
              </div>
            )}

            {section === "privacy" && (
              <section>
                <h2 className="text-lg font-semibold text-ink">Privacy</h2>
                <p className="mt-1 text-sm text-ink-muted">
                  Controls what leaves this computer during Scan.
                </p>

                <div className="mt-4 overflow-hidden rounded-lg border border-line bg-surface">
                  <div className="flex items-start justify-between gap-4 px-4 py-4">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-medium text-ink">
                          Privacy pre-check
                        </h3>
                        <span
                          className={[
                            "rounded px-1.5 py-0.5 text-xs font-semibold uppercase tracking-wide",
                            enabled
                              ? "bg-accent-soft text-ink"
                              : "bg-label-orange/15 text-label-orange",
                          ].join(" ")}
                        >
                          {enabled ? "On" : "Off"}
                        </span>
                        {savedFlash && (
                          <span className="text-xs font-medium text-ink-muted">
                            Saved
                          </span>
                        )}
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                        Before Gemini tags a photo, TagPhy runs a local screen
                        for intimate content and likely PII (IDs, forms,
                        screenshots). Flagged files are skipped: not tagged, not
                        uploaded, not moved. This is best-effort, not a
                        guarantee.
                      </p>
                    </div>
                    <Switch
                      checked={enabled}
                      disabled={toggleDisabled}
                      onChange={onToggle}
                      label="Privacy pre-check"
                    />
                  </div>

                  <div className="border-t border-line bg-panel/60 px-4 py-3 text-sm text-ink-muted">
                    {scanLocked ? (
                      <p>Locked while a scan is running.</p>
                    ) : enabled ? (
                      <p>
                        Photos that pass the screen are still tagged online with
                        Gemini.
                      </p>
                    ) : (
                      <p className="text-label-orange">
                        Every scanned photo may be sent to Gemini, including
                        intimate or document shots mixed into unsorted folders.
                      </p>
                    )}
                  </div>
                </div>
              </section>
            )}

            {section === "about" && (
              <section>
                <h2 className="text-lg font-semibold text-ink">About</h2>
                <p className="mt-1 text-sm text-ink-muted">
                  This installation lives on the drive TagPhy is running from.
                </p>

                <div className="mt-4 overflow-hidden rounded-lg border border-line bg-surface">
                  <dl className="divide-y divide-line text-sm">
                    <div className="flex justify-between gap-4 px-4 py-3">
                      <dt className="text-ink-muted">Application</dt>
                      <dd className="font-medium text-ink">TagPhy</dd>
                    </div>
                    <div className="flex justify-between gap-4 px-4 py-3">
                      <dt className="text-ink-muted">Version</dt>
                      <dd className="font-medium text-ink">0.1.0</dd>
                    </div>
                    <div className="flex justify-between gap-4 px-4 py-3">
                      <dt className="text-ink-muted">Vision tagging</dt>
                      <dd className="font-medium text-ink">Gemini (online)</dd>
                    </div>
                    <div className="flex justify-between gap-4 px-4 py-3">
                      <dt className="text-ink-muted">Settings storage</dt>
                      <dd className="text-right font-medium text-ink">
                        tagphy.db on this drive
                      </dd>
                    </div>
                  </dl>
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
