import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchTagPictures } from "../api/client";
import type { TagPictureResponse } from "../api/types";
import { Preview } from "../components/Preview";

export function TagPicturesPage() {
  const { tagId } = useParams();
  const id = Number(tagId);
  const [tag, setTag] = useState<TagPictureResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(id)) {
      setError("Invalid tag id");
      return;
    }
    let cancelled = false;
    setError(null);
    setTag(null);
    fetchTagPictures(id)
      .then((data) => {
        if (!cancelled) setTag(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load tag");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  return (
    <div className="w-full px-4 py-6 library:px-8">
      <Link
        to="/library"
        className="inline-flex items-center rounded bg-accent px-3 py-1.5 text-base font-medium text-on-accent hover:brightness-110"
      >
        ← Library
      </Link>

      {error && (
        <div className="mt-4 rounded-md border border-label-orange/40 bg-surface px-3 py-2 text-base">
          <span className="font-medium text-label-orange">
            Couldn’t load tag.
          </span>
          <div className="mt-1 font-mono text-sm text-ink-muted">{error}</div>
        </div>
      )}

      {!error && !tag && (
        <p className="mt-4 text-base text-ink-muted">Loading…</p>
      )}

      {tag && (
        <>
          <h1 className="mt-3 text-2xl font-semibold text-ink">{tag.name}</h1>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="rounded bg-label-blue px-2 py-0.5 text-sm font-medium text-on-chip">
              {tag.pictures?.length} photos
            </span>
            <span className="rounded bg-label-pink px-2 py-0.5 text-sm font-medium text-on-chip">
              {tag.children.length} child tags
            </span>
            <span className="rounded bg-label-yellow px-2 py-0.5 text-sm font-medium text-on-chip">
              {tag.source}
            </span>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <RelationList title="Parents" items={tag.parents} />
            <RelationList title="Children" items={tag.children} />
          </div>

          <section className="mt-8 rounded-md border border-dashed border-line bg-surface px-4 py-8 text-center">
            <Preview
              pictures={tag.pictures || []}
              page={1}
              onPageChange={() => {}}
            />
          </section>
        </>
      )}
    </div>
  );
}

function RelationList({
  title,
  items,
}: {
  title: string;
  items: { id: number; name: string }[];
}) {
  return (
    <section className="rounded-md border border-line bg-surface p-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted">
        {title}
      </h2>
      {items.length === 0 ? (
        <p className="mt-2 text-base text-ink-muted">None</p>
      ) : (
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {items.map((item) => (
            <li key={item.id}>
              <Link
                to={`/tags/${item.id}/pictures`}
                className="inline-block rounded px-2.5 py-1 text-base text-accent ring-1 ring-line hover:bg-accent-soft"
              >
                {item.name}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
