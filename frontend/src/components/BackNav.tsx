import { Link, useLocation, useNavigate } from "react-router-dom";

type Props = {
  fallback?: string;
  fallbackLabel?: string;
  className?: string;
};

const DEFAULT_LINK_CLASS =
  "inline-flex items-center gap-1.5 text-base font-medium text-ink-muted transition-colors hover:text-accent";

/**
 * Browser back when the user arrived from another in-app route; otherwise link to fallback.
 * Uses location.key — initial entry is "default" (direct open / refresh).
 */
export function BackNav({
  fallback = "/library",
  fallbackLabel = "Library",
  className = DEFAULT_LINK_CLASS,
}: Props) {
  const navigate = useNavigate();
  const location = useLocation();
  const canGoBack = location.key !== "default";

  if (canGoBack) {
    return (
      <button type="button" onClick={() => navigate(-1)} className={className}>
        <span aria-hidden>←</span>
        Back
      </button>
    );
  }

  return (
    <Link to={fallback} className={className}>
      <span aria-hidden>←</span>
      {fallbackLabel}
    </Link>
  );
}
