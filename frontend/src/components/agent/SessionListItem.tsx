type Props = {
  title: string
  isActive: boolean
  onClick: () => void
}

export function SessionListItem({ title, isActive, onClick }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'w-full rounded-md px-2.5 py-2 text-left text-xs transition-colors library:px-3 library:text-sm',
        isActive
          ? 'bg-accent-soft font-medium text-ink'
          : 'text-ink-muted hover:bg-surface hover:text-ink',
      ].join(' ')}
    >
      <span className="line-clamp-2 break-words">{title}</span>
    </button>
  )
}
