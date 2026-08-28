import { useEffect, useRef, useState } from 'react'
import type { ChatMessage } from '../../api/agent'
import { ChatBubble } from './ChatBubble'

type Props = {
  messages: ChatMessage[]
  loading: boolean
  onSend: (text: string) => void
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="rounded-2xl rounded-bl-sm border border-line bg-surface px-3 py-3 sm:px-4">
        <span className="inline-flex items-center gap-1" aria-label="Agent is typing">
          <span className="h-2 w-2 animate-pulse rounded-full bg-ink-muted [animation-delay:0ms]" />
          <span className="h-2 w-2 animate-pulse rounded-full bg-ink-muted [animation-delay:150ms]" />
          <span className="h-2 w-2 animate-pulse rounded-full bg-ink-muted [animation-delay:300ms]" />
        </span>
      </div>
    </div>
  )
}

export function ChatWindow({ messages, loading, onSend }: Props) {
  const [draft, setDraft] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function handleSubmit() {
    const text = draft.trim()
    if (!text || loading) return
    setDraft('')
    onSend(text)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex h-full min-h-0 min-w-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-4 sm:px-4 sm:py-6 library:px-8">
        {messages.length === 0 && !loading ? (
          <div className="flex h-full items-center justify-center px-2">
            <div className="max-w-md text-center">
              <i
                className="fa-solid fa-wand-magic-sparkles mb-3 text-2xl text-ink-muted sm:mb-4 sm:text-3xl library:text-4xl"
                aria-hidden
              />
              <h2 className="text-base font-semibold text-ink sm:text-lg library:text-xl">
                Photo Finder
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted sm:text-base library:text-lg">
                Ask me to find photos in your catalog. Describe what you are
                looking for and I will search by tags and visual similarity.
              </p>
            </div>
          </div>
        ) : (
          <div className="mx-auto flex w-full min-w-0 max-w-3xl flex-col gap-3 sm:gap-4 library:max-w-4xl">
            {messages.map((msg, i) => (
              <ChatBubble key={i} message={msg} />
            ))}
            {loading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-line bg-panel px-3 py-3 sm:px-4 sm:py-4 library:px-8">
        <div className="mx-auto flex w-full min-w-0 max-w-3xl items-end gap-2 sm:gap-3 library:max-w-4xl">
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your photos…"
            rows={1}
            disabled={loading}
            className="min-h-[2.5rem] min-w-0 flex-1 resize-none rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:border-accent focus:outline-none disabled:opacity-60 sm:min-h-[2.75rem] sm:px-4 sm:py-2.5 sm:text-base library:text-[1.05rem]"
          />
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading || draft.trim().length === 0}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent text-on-accent transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40 sm:h-11 sm:w-11"
            aria-label="Send message"
          >
            <i className="fa-solid fa-paper-plane text-sm sm:text-base" aria-hidden />
          </button>
        </div>
      </div>
    </div>
  )
}
