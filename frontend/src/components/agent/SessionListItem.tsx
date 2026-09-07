type Props = {
  title: string;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
};

export function SessionListItem({ title, isActive, onClick, onDelete }: Props) {
  return (
    <div
      className={[
        "group flex w-full items-center gap-1 rounded-md px-2.5 py-2 text-xs transition-colors library:px-3 library:text-sm",
        isActive
          ? "bg-accent-soft font-medium text-ink"
          : "text-ink-muted hover:bg-surface hover:text-ink",
      ].join(" ")}
    >
      <button
        type="button"
        onClick={onClick}
        className="min-w-0 flex-1 text-left"
      >
        <span className="line-clamp-2 break-words">{title}</span>
      </button>

      <button
        type="button"
        onClick={onDelete}
        aria-label={`Delete ${title}`}
        className="shrink-0 rounded p-1 text-ink-muted opacity-100 transition-opacity hover:bg-accent-soft hover:text-ink focus-visible:opacity-100 library:opacity-0 library:group-hover:opacity-100"
      >
        <i className="fa-solid fa-trash text-[0.7rem]" aria-hidden />
      </button>
    </div>
  );
}
