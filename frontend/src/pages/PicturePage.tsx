import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchPictureDetail } from "../api/client";
import type { PictureDetail } from "../api/types";
import { BackNav } from "../components/BackNav";

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
    <div className="w-full px-4 py-6 library:px-8">
      <div className="mx-auto w-full max-w-3xl animate-fade-up">
        <BackNav />

        <article className="mt-5 overflow-hidden rounded-xl border border-line/80 bg-surface shadow-[0_1px_2px_rgba(42,31,26,0.04),0_12px_28px_-12px_rgba(42,31,26,0.18)]">
          {/* Print stage — dark mat so letterboxing feels intentional */}
          <figure className="relative bg-header px-3 py-3 library:px-5 library:py-5">
            <div className="overflow-hidden rounded-md bg-header ring-1 ring-white/10">
              <img
                src={`/api/pictures/${picture.id}/preview?size=1280`}
                alt={picture.file_name}
                className="mx-auto block max-h-[min(62vh,34rem)] w-full object-contain"
              />
            </div>
          </figure>

          {/* Caption sheet */}
          <div className="px-5 py-6 library:px-8 library:py-7">
            <header>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-muted">
                Photo
              </p>
              <h1 className="mt-1.5 break-words text-[1.85rem] font-semibold leading-tight tracking-tight text-ink library:text-[2.05rem]">
                {picture.file_name}
              </h1>
              {picture.description ? (
                <p className="mt-3 max-w-prose text-lg leading-[1.65] text-ink-muted">
                  {picture.description}
                </p>
              ) : null}
            </header>

            {(picture.year || picture.location) && (
              <dl className="mt-6 grid gap-4 border-t border-line/70 pt-5 sm:grid-cols-2">
                {picture.year ? (
                  <div>
                    <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-ink-muted">
                      Year
                    </dt>
                    <dd className="mt-1 text-lg font-medium text-ink">
                      {picture.year}
                    </dd>
                  </div>
                ) : null}
                {picture.location ? (
                  <div>
                    <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-ink-muted">
                      Location
                    </dt>
                    <dd className="mt-1 text-lg font-medium text-ink">
                      {picture.location}
                    </dd>
                  </div>
                ) : null}
              </dl>
            )}

            <section className="mt-6 border-t border-line/70 pt-5">
              <h2 className="text-xs font-semibold uppercase tracking-[0.12em] text-ink-muted">
                Tags
                {picture.tags.length > 0 ? (
                  <span className="ml-2 font-medium normal-case tracking-normal text-ink-muted/80">
                    {picture.tags.length}
                  </span>
                ) : null}
              </h2>

              {picture.tags.length === 0 ? (
                <p className="mt-3 text-base text-ink-muted">No tags yet</p>
              ) : (
                <ul className="mt-3.5 flex flex-wrap gap-x-1 gap-y-2">
                  {picture.tags.map((tag) => (
                    <li key={tag.id}>
                      <Link
                        to={`/tags/${tag.id}/pictures`}
                        className="inline-block rounded-md px-2.5 py-1 text-base text-accent transition-colors hover:bg-accent-soft"
                      >
                        {tag.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </article>
      </div>
    </div>
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
        <p className="mt-7 text-2xl font-medium text-ink">Loading photo…</p>
        <p className="mt-2 text-lg leading-snug text-ink-muted">
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
        <h1 className="text-3xl font-semibold text-ink">Couldn&apos;t load photo.</h1>
        <div className="mt-4 rounded-md border border-label-orange/40 bg-surface px-3 py-2 text-lg">
          <span className="font-medium text-label-orange">
            Something went wrong.
          </span>
          <div className="mt-1 font-mono text-base text-ink-muted">{message}</div>
        </div>
        <BackNav
          className="mt-6 inline-flex items-center rounded bg-accent px-3 py-1.5 text-lg font-medium text-on-accent hover:brightness-110"
        />
      </div>
    </div>
  );
}
