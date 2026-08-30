import { Link } from "react-router-dom";
import type { Picture } from "../api/types";

type Props = {
  picture: Picture;
};

/** Fixed 160 CSS px — at or below backend 320px thumb, sharp on 2x displays. */
export function PreviewItem({ picture }: Props) {
  return (
    <figure className="w-40 shrink-0 overflow-hidden rounded-md border border-line bg-surface">
      <Link to={`/pictures/${picture.id}`}>
        <img
          src={`/api/pictures/${picture.id}/preview`}
          alt={picture.file_name}
          loading="lazy"
          width={160}
          height={160}
          className="block h-40 w-40 object-cover"
        />
        <figcaption className="truncate px-2 py-1.5 text-xs text-ink-muted">
          {picture.file_name}
        </figcaption>
      </Link>
    </figure>
  );
}
