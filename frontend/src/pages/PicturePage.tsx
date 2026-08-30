import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchPictureDetail } from "../api/client";
import type { PictureDetail } from "../api/types";

export function PicturePage() {
  const { pictureId } = useParams();
  const [picture, setPicture] = useState<PictureDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pictureId || !Number.isFinite(Number(pictureId))) {
      return;
    }
    let cancelled = false;
    setError(null);
    setPicture(null);
    fetchPictureDetail(Number(pictureId))
      .then((data) => {
        if (!cancelled) setPicture(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setPicture(null);
          setError(
            err instanceof Error ? err.message : "Failed to load picture",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [pictureId]);

  if (!pictureId || !Number.isFinite(Number(pictureId))) {
    return <ErrorView message="Invalid picture id" />;
  }

  if (error) {
    return <ErrorView message={error} />;
  }

  if (!picture) {
    return <LoadingView />;
  }

  return (
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
}

function LoadingView() {
  return (
    <div className="flex min-h-[min(100%,32rem)] flex-col items-center justify-center px-4 py-12">
      <div className="flex w-72 flex-col items-center text-center">
        <div className="relative h-[4.5rem] w-[4.5rem]" aria-hidden>
          <div className="absolute inset-0 rounded-full border-[3px] border-accent/15" />
          <div className="absolute inset-0 animate-spin rounded-full border-[3px] border-transparent border-t-accent border-r-accent/40" />
        </div>
        <p className="mt-7 text-xl font-medium text-ink">Loading photo…</p>
        <p className="mt-2 text-base leading-snug text-ink-muted">
          Digging through the pile.
          <br />
          Hang tight.
        </p>
      </div>
    </div>
  );
}

function ErrorView({ message }: { message: string }) {
  return (
    <div className="w-full px-4 py-6 library:px-8">
      <div className="mx-auto max-w-lg">
        <h1 className="text-2xl font-semibold text-ink">Couldn&apos;t load photo.</h1>
        <div className="mt-4 rounded-md border border-label-orange/40 bg-surface px-3 py-2 text-base">
          <span className="font-medium text-label-orange">
            Something went wrong.
          </span>
          <div className="mt-1 font-mono text-sm text-ink-muted">{message}</div>
        </div>
        <Link
          to="/library"
          className="mt-6 inline-flex items-center rounded bg-accent px-3 py-1.5 text-base font-medium text-on-accent hover:brightness-110"
        >
          ← Library
        </Link>
      </div>
    </div>
  );
}
