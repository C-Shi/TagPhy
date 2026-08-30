import { Link } from "react-router-dom";

import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { PictureDetail } from "../api/types";
import { fetchPictureDetail } from "../api/client";

export function PicturePage() {
  const { pictureId } = useParams();
  const [picture, setPicture] = useState<PictureDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pictureId) {
      return;
    }
    let cancelled = false;
    setError(null);
    fetchPictureDetail(Number(pictureId))
      .then((data) => {
        if (!cancelled) setPicture(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setPicture(null);
          setError(err instanceof Error ? err.message : "Failed to load tags");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [pictureId]);

  const pictureDetail = picture && (
    <>
      <figure className="w-40 shrink-0 overflow-hidden rounded-md border border-line bg-surface">
        <Link to={`/pictures/${picture.id}`}>
          <img
            src={`/api/pictures/${picture.id}/preview?size=1280`}
            alt={picture.file_name}
            loading="lazy"
            width={1280}
            height={1280}
            className="block h-40 w-40 object-cover"
          />
          <figcaption className="truncate px-2 py-1.5 text-xs text-ink-muted">
            {picture.file_name}
          </figcaption>
        </Link>
      </figure>
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-bold">{picture.file_name}</h1>
        <p className="text-sm text-ink-muted">{picture.description}</p>
      </div>

      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-bold">Tags</h2>
        <ul className="flex flex-wrap gap-2">
          {picture.tags.map((tag) => (
            <li key={tag.id}>
              <Link to={`/tags/${tag.id}/pictures`}>{tag.name}</Link>
            </li>
          ))}
        </ul>
      </div>
    </>
  );

  if (error) {
    return <div>{error}</div>;
  }

  if (picture) {
    return <>{pictureDetail}</>;
  }

  return <div>Loading...</div>;
}
