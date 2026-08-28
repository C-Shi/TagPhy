import type { AgentSearchItem } from '../../api/agent'

type Props = {
  items: AgentSearchItem[]
}

export function SearchResultsGrid({ items }: Props) {
  if (items.length === 0) return null

  return (
    <div className="mt-3 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:gap-3">
      {items.map((item) => (
        <figure
          key={item.id}
          className="min-w-0 overflow-hidden rounded-md border border-line bg-surface sm:w-36 library:w-40"
        >
          <img
            src={item.preview_url}
            alt={item.description}
            loading="lazy"
            className="aspect-square w-full object-cover"
          />
          <figcaption className="space-y-0.5 px-2 py-1.5">
            <p className="line-clamp-2 break-words text-xs text-ink sm:text-sm">
              {item.description}
            </p>
            <p className="text-[0.65rem] text-ink-muted sm:text-xs">
              {Math.round(item.similarity * 100)}% match
            </p>
          </figcaption>
        </figure>
      ))}
    </div>
  )
}
