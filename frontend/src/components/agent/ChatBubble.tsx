import type { ChatMessage } from "../../api/agents";
import { SearchResultsGrid } from "./SearchResultsGrid";

type Props = {
  message: ChatMessage;
};

const bubbleBase =
  "min-w-0 break-words rounded-2xl px-3 py-2 text-sm leading-relaxed sm:px-4 sm:py-2.5 sm:text-base library:text-[1.05rem]";

export function ChatBubble({ message }: Props) {
  if (message.role === "user") {
    return (
      <div className="flex min-w-0 justify-end">
        <div
          className={`max-w-[min(100%,28rem)] rounded-br-sm bg-accent text-on-accent sm:max-w-[85%] library:max-w-[80%] ${bubbleBase}`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  if (message.role === "error") {
    return (
      <div className="flex min-w-0 justify-start">
        <div
          className={`max-w-[min(100%,28rem)] rounded-bl-sm border border-label-orange/50 bg-surface text-label-orange sm:max-w-[85%] library:max-w-[80%] ${bubbleBase}`}
        >
          <p className="whitespace-pre-wrap">
            <i className="fa-solid fa-circle-exclamation mr-1.5" aria-hidden />
            {message.content}
          </p>
        </div>
      </div>
    );
  }

  const { turn } = message;
  const showText = turn.message != null && turn.message.trim().length > 0;
  const showResults =
    turn.kind === "search_results" && turn.results?.items != null;

  return (
    <div className="flex min-w-0 justify-start">
      <div
        className={`max-w-[min(100%,32rem)] rounded-bl-sm border border-line bg-surface text-ink sm:max-w-[90%] library:max-w-[85%] ${bubbleBase}`}
      >
        {showText && <p className="whitespace-pre-wrap">{turn.message}</p>}
        {!showText && !showResults && (
          <p className="text-ink-muted">No response.</p>
        )}
        {showResults && <SearchResultsGrid items={turn.results!.items} />}
      </div>
    </div>
  );
}
