import type { Picture } from "../api/types";
import { PreviewItem } from "./PreviewItem";

const DEFAULT_PAGE_SIZE = 25;
const LIBRARY_EMPTY_HINT =
  "Scan photos or clear filters to see previews here.";
const TAG_EMPTY_HINT =
  "No photos tagged with this tag or its child tags.";

type Props = {
  pictures: Picture[];
  page: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
  /** `library` = side panel (default). `tag` = full-width responsive grid on tag page. */
  variant?: "library" | "tag";
  emptyHint?: string;
};

export function Preview({
  pictures,
  page,
  onPageChange,
  pageSize = DEFAULT_PAGE_SIZE,
  variant = "library",
  emptyHint,
}: Props) {
  const isTag = variant === "tag";
  const hasPrev = page > 1;
  const hasNext = pictures.length >= pageSize;
  const showPagination = hasPrev || hasNext;
  const hint =
    emptyHint ??
    (isTag ? TAG_EMPTY_HINT : LIBRARY_EMPTY_HINT);

  const paginationBar = showPagination && (
    <div
      className={
        isTag
          ? "mt-4 flex items-center justify-between gap-3 border-t border-line pt-4"
          : "shrink-0 border-t border-line bg-panel px-4 py-3 library:px-6"
      }
    >
      <div className="flex w-full items-center justify-between gap-3">
        <button
          type="button"
          disabled={!hasPrev}
          onClick={() => onPageChange(page - 1)}
          className={[
            "rounded px-3 py-1.5 text-sm font-semibold transition-colors",
            hasPrev
              ? "bg-surface text-ink ring-1 ring-line hover:bg-accent-soft"
              : "cursor-not-allowed bg-surface/60 text-ink-muted opacity-50",
          ].join(" ")}
        >
          Previous
        </button>

        <span
          className="text-sm font-medium text-ink-muted"
          aria-live="polite"
        >
          Page {page}
        </span>

        <button
          type="button"
          disabled={!hasNext}
          onClick={() => onPageChange(page + 1)}
          className={[
            "rounded px-3 py-1.5 text-sm font-semibold transition-colors",
            hasNext
              ? "bg-accent text-on-accent hover:brightness-110"
              : "cursor-not-allowed bg-surface/60 text-ink-muted opacity-50",
          ].join(" ")}
        >
          Next
        </button>
      </div>
    </div>
  );

  const emptyState = (
    <div
      className={[
        "flex flex-col items-center justify-center rounded-md border border-dashed border-line bg-surface px-4 py-12 text-center",
        isTag ? "" : "mt-6",
      ].join(" ")}
    >
      <p className="text-base font-semibold text-ink">No photos</p>
      <p className="mt-1 text-sm text-ink-muted">{hint}</p>
    </div>
  );

  const grid = (
    <div
      className={
        isTag
          ? "grid grid-cols-[repeat(auto-fill,minmax(12rem,1fr))] gap-3 sm:gap-4"
          : "mt-4 flex flex-wrap content-start gap-3"
      }
    >
      {pictures.map((picture) => (
        <PreviewItem key={picture.id} picture={picture} variant={variant} />
      ))}
    </div>
  );

  if (isTag) {
    return (
      <div className="mt-2">
        {pictures.length === 0 ? emptyState : grid}
        {paginationBar}
      </div>
    );
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col bg-canvas/40">
      <div className="min-h-0 flex-1 overflow-auto px-4 py-4 library:px-6">
        {pictures.length === 0 ? emptyState : grid}
      </div>
      {paginationBar}
    </div>
  );
}
