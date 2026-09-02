import { Link } from "react-router-dom";
import type { Picture } from "../api/types";

type Props = {
  picture: Picture;
  variant?: "library" | "tag";
};

export function PreviewItem({ picture, variant = "library" }: Props) {
  const isTag = variant === "tag";

  return (
    <figure
      className={[
        "overflow-hidden border border-line bg-surface",
        isTag
          ? "rounded-lg transition hover:shadow-md hover:ring-1 hover:ring-accent/30"
          : "w-40 shrink-0 rounded-md",
      ].join(" ")}
    >
      <Link
        to={`/pictures/${picture.id}`}
        className={isTag ? "block" : undefined}
      >
        <img
          src={`/api/pictures/${picture.id}/preview`}
          alt={picture.file_name}
          loading="lazy"
          width={isTag ? undefined : 160}
          height={isTag ? undefined : 160}
          className={
            isTag
              ? "aspect-square w-full object-cover"
              : "block h-40 w-40 object-cover"
          }
        />
        <figcaption className="truncate px-2 py-1.5 text-xs text-ink-muted">
          {picture.file_name}
        </figcaption>
      </Link>
    </figure>
  );
}
