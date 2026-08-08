import { NavLink, Outlet } from 'react-router-dom'

const upcoming = ['Scan', 'Agent', 'Settings'] as const

export function AppShell() {
  return (
    <div className="flex h-full min-h-0 flex-col bg-canvas text-ink">
      <header className="shrink-0 border-b border-line bg-surface">
        <div className="flex h-14 items-center gap-6 px-8">
          <div className="text-xl font-semibold tracking-tight text-ink">
            TagPhy
          </div>
          <nav className="flex items-center gap-1 text-base">
            <NavLink
              to="/tags"
              className={({ isActive }) =>
                [
                  'rounded px-3 py-1.5 font-medium',
                  isActive
                    ? 'bg-accent-soft text-accent'
                    : 'text-ink-muted hover:bg-accent-soft/60 hover:text-ink',
                ].join(' ')
              }
            >
              Library
            </NavLink>
            {upcoming.map((label) => (
              <span
                key={label}
                title="Coming soon"
                className="cursor-not-allowed rounded px-3 py-1.5 text-ink-muted/55"
                aria-disabled="true"
              >
                {label}
                <span className="ml-1.5 text-xs font-medium uppercase tracking-wide text-label-orange">
                  Soon
                </span>
              </span>
            ))}
          </nav>
        </div>
        <div className="flex h-9 items-center border-t border-line/80 bg-canvas/60 px-8 text-sm text-ink-muted">
          <span className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-1.5 w-1.5 rounded-full bg-label-blue"
              aria-hidden
            />
            Gemini Connected
          </span>
        </div>
      </header>

      <main className="min-h-0 flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
