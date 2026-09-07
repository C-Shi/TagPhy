import type { AgentSession } from "../../api/agents";
import { SessionListItem } from "./SessionListItem";

type Props = {
  sessions: AgentSession[];
  activeSessionId: string | undefined;
  deleteError: string | null;
  onDismissDeleteError: () => void;
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
};

export function SessionList({
  sessions,
  activeSessionId,
  deleteError,
  onDismissDeleteError,
  onNewChat,
  onSelectSession,
  onDeleteSession,
}: Props) {
  const sorted = [...sessions].sort((a, b) => b.createdAt - a.createdAt);

  return (
    <aside className="flex min-w-0 shrink-0 flex-col border-b border-line bg-panel library:h-full library:w-56 library:border-b-0 library:border-r">
      <div className="shrink-0 border-b border-line p-2 library:p-3">
        <button
          type="button"
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-md border border-line bg-surface px-3 py-2 text-xs font-medium text-ink transition-colors hover:bg-accent-soft library:text-sm"
        >
          <i className="fa-solid fa-plus text-xs" aria-hidden />
          New Chat
        </button>
      </div>
      {deleteError && (
        <div
          role="alert"
          className="mx-2 mt-2 rounded-md border border-label-orange/40 bg-accent-soft px-2.5 py-2 text-xs text-ink library:mx-3 library:text-sm"
        >
          <div className="flex items-start justify-between gap-2">
            <span className="min-w-0 flex-1 break-words">{deleteError}</span>
            <button
              type="button"
              onClick={onDismissDeleteError}
              aria-label="Dismiss"
              className="shrink-0 rounded p-0.5 text-ink-muted hover:text-ink"
            >
              <i className="fa-solid fa-xmark text-xs" aria-hidden />
            </button>
          </div>
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-x-auto overflow-y-hidden p-2 library:overflow-x-hidden library:overflow-y-auto">
        {sorted.length === 0 ? (
          <p className="px-2 py-3 text-center text-xs text-ink-muted library:py-4">
            No conversations yet
          </p>
        ) : (
          <ul className="flex gap-2 library:flex-col library:gap-1">
            {sorted.map((session) => (
              <li
                key={session.id}
                className="w-36 shrink-0 library:w-auto library:shrink"
              >
                <SessionListItem
                  title={session.title}
                  isActive={session.id === activeSessionId}
                  onClick={() => onSelectSession(session.id)}
                  onDelete={() => onDeleteSession(session.id)}
                />
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
