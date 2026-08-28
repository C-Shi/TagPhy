import { useState } from "react"
import { NavLink, Outlet, useLocation } from "react-router-dom"
import { AgentSessionProvider } from "./agent/AgentSessionContext"
import { ScanLockContext } from "./ScanLockContext"

function navClass(isActive: boolean) {
  return [
    "rounded px-3 py-1.5 font-medium",
    isActive
      ? "bg-accent text-on-accent"
      : "text-header-muted hover:bg-white/10 hover:text-on-accent",
  ].join(" ")
}

export function AppShell() {
  const [scanLocked, setScanLocked] = useState(false)
  const location = useLocation()
  const agentActive = location.pathname.startsWith("/agent")

  return (
    <ScanLockContext.Provider value={{ scanLocked, setScanLocked }}>
      <AgentSessionProvider>
      <div className="flex h-full min-h-0 flex-col bg-canvas text-ink">
        <header className="shrink-0 bg-header text-on-accent">
          <div className="flex h-14 items-center gap-6 px-4 library:px-8">
            <div className="text-xl font-semibold tracking-tight text-on-accent">
              TagPhy
            </div>
            <nav className="flex min-w-0 flex-wrap items-center gap-1 text-base">
              {scanLocked ? (
                <span
                  title="Scan in progress"
                  className="inline-flex cursor-not-allowed items-center rounded px-3 py-1.5 text-header-muted/70"
                  aria-disabled="true"
                >
                  Library
                </span>
              ) : (
                <NavLink
                  to="/library"
                  className={({ isActive }) => navClass(isActive)}
                >
                  Library
                </NavLink>
              )}
              <NavLink to="/scan" className={({ isActive }) => navClass(isActive)}>
                Scan
              </NavLink>
              <NavLink
                to="/settings"
                className={({ isActive }) => navClass(isActive)}
              >
                Settings
              </NavLink>
              <NavLink
                to="/agent"
                className={() => navClass(agentActive)}
              >
                Agent
              </NavLink>
            </nav>
          </div>
          <div className="flex h-9 items-center border-t border-white/10 bg-black/20 px-4 text-sm text-header-muted library:px-8">
            <span className="inline-flex items-center gap-1.5">
              <span
                className="inline-block h-1.5 w-1.5 rounded-full bg-label-blue"
                aria-hidden
              />
              Gemini Connected
            </span>
          </div>
        </header>

        <main className="min-h-0 flex-1 overflow-auto bg-panel">
          <Outlet />
        </main>
      </div>
      </AgentSessionProvider>
    </ScanLockContext.Provider>
  )
}
