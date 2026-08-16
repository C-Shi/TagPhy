type ConfirmModalProps = {
  title: string
  message: string
  confirmLabel: string
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmModal({
  title,
  message,
  confirmLabel,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  return (
    <div
      className="fixed inset-0 z-20 flex items-center justify-center bg-header/50 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
    >
      <div className="w-full max-w-md rounded-md border border-line bg-surface px-4 py-4">
        <h2 id="confirm-title" className="text-lg font-semibold text-ink">
          {title}
        </h2>
        <p className="mt-2 text-base text-ink-muted">{message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded bg-accent px-3 py-1.5 text-base font-medium text-on-accent hover:brightness-110"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded bg-label-orange px-3 py-1.5 text-base font-semibold text-on-chip hover:brightness-110"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
