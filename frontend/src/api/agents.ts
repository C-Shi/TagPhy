export type AgentSearchItem = {
  id: number
  description: string
  preview_url: string
  similarity: number
}

export type AgentSearchResults = {
  type: 'search_results'
  query: string
  items: AgentSearchItem[]
}

export type AgentTurnResponse = {
  kind: 'search_results' | 'chat'
  message: string | null
  results: AgentSearchResults | null
}

export type PhotoFinderResponse = {
  response: AgentTurnResponse
  session: string
}

export type ChatMessage =
  | { role: 'user'; content: string }
  | { role: 'agent'; turn: AgentTurnResponse }
  | { role: 'error'; content: string }

export type AgentSession = {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: number
}

/**
 * Wire types — field names match BE/ADK JSON as emitted (FE follows BE).
 * ADK Session/Event serialize as camelCase; session.state keys stay snake_case.
 */
type AdkSessionState = {
  chat_title?: string
  search_query?: string
  [key: string]: unknown
}

type AdkContentPart = {
  text?: string | null
  functionCall?: { name?: string; args?: unknown } | null
  functionResponse?: {
    name?: string
    response?: Record<string, unknown>
  } | null
}

type AdkEvent = {
  author?: string
  invocationId?: string
  partial?: boolean | null
  longRunningToolIds?: string[] | null
  content?: { role?: string; parts?: AdkContentPart[] } | null
  actions?: { skipSummarization?: boolean | null; [key: string]: unknown }
}

type AdkSession = {
  id: string
  state?: AdkSessionState | null
  events?: AdkEvent[] | null
  lastUpdateTime?: number | null
}

type AdkListSessionsResponse = {
  sessions: AdkSession[]
}

const RANK_TOOL_NAME = 'tool_rank_photos'
const SEARCH_RESULTS_TYPE = 'search_results'

async function parseAgentError(res: Response): Promise<never> {
  const body = await res.text().catch(() => '')
  let detail = body
  try {
    const parsed = JSON.parse(body) as { detail?: string }
    if (typeof parsed.detail === 'string') detail = parsed.detail
  } catch {
    // use raw body
  }
  throw new Error(
    detail || `API request failed (${res.status} ${res.statusText})`,
  )
}

/** POST /api/agents/photo-finder */
export async function sendPhotoFinderMessage(
  message: string,
  sessionId?: string,
): Promise<PhotoFinderResponse> {
  const res = await fetch('/api/agents/photo-finder', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId ?? null,
    }),
  })
  if (!res.ok) await parseAgentError(res)
  return res.json() as Promise<PhotoFinderResponse>
}

export function truncateTitle(text: string, maxLen = 40): string {
  const trimmed = text.trim()
  if (trimmed.length <= maxLen) return trimmed
  return `${trimmed.slice(0, maxLen - 1)}…`
}

export function sessionTitleFromState(
  state: AdkSessionState | null | undefined,
  firstUserText?: string,
): string {
  const chatTitle = state?.chat_title?.trim()
  if (chatTitle) return chatTitle

  const searchQuery = state?.search_query?.trim()
  if (searchQuery) return truncateTitle(searchQuery)

  const firstUser = firstUserText?.trim()
  if (firstUser) return truncateTitle(firstUser)

  return 'New chat'
}

function partText(parts: AdkContentPart[] | undefined): string | null {
  if (!parts) return null
  for (const part of parts) {
    if (part.text) return part.text
  }
  return null
}

function getFunctionResponses(event: AdkEvent) {
  const out: NonNullable<AdkContentPart['functionResponse']>[] = []
  for (const part of event.content?.parts ?? []) {
    if (part.functionResponse) out.push(part.functionResponse)
  }
  return out
}

function getFunctionCalls(event: AdkEvent) {
  const out: NonNullable<AdkContentPart['functionCall']>[] = []
  for (const part of event.content?.parts ?? []) {
    if (part.functionCall) out.push(part.functionCall)
  }
  return out
}

/** Mirror ADK Event.is_final_response for JSON payloads. */
function isFinalResponse(event: AdkEvent): boolean {
  if (event.actions?.skipSummarization || event.longRunningToolIds?.length) {
    return true
  }
  return (
    getFunctionCalls(event).length === 0 &&
    getFunctionResponses(event).length === 0 &&
    !event.partial
  )
}

function extractPhotoFinderTurn(events: AdkEvent[]): AgentTurnResponse {
  let results: AgentSearchResults | null = null
  let message: string | null = null

  for (const event of events) {
    for (const fr of getFunctionResponses(event)) {
      if (fr.name !== RANK_TOOL_NAME || !fr.response) continue
      const resp = fr.response
      if (resp.type === SEARCH_RESULTS_TYPE) {
        results = resp as unknown as AgentSearchResults
      } else if (
        typeof resp.result === 'object' &&
        resp.result !== null &&
        (resp.result as Record<string, unknown>).type === SEARCH_RESULTS_TYPE
      ) {
        results = resp.result as unknown as AgentSearchResults
      }
    }

    if (isFinalResponse(event) && event.content) {
      const text = partText(event.content.parts)
      if (text) message = text
    }
  }

  if (results !== null) {
    return { kind: 'search_results', message, results }
  }
  return { kind: 'chat', message, results: null }
}

/** Map ordered ADK events → slim ChatMessage[] for the FE store. */
export function eventsToChatMessages(events: AdkEvent[]): ChatMessage[] {
  const messages: ChatMessage[] = []
  let i = 0

  while (i < events.length) {
    const event = events[i]
    if (event.author === 'user') {
      const text = partText(event.content?.parts)
      if (text) {
        messages.push({ role: 'user', content: text })
      }
      i += 1

      const invocationId = event.invocationId
      const turnEvents: AdkEvent[] = []
      while (i < events.length && events[i].author !== 'user') {
        const next = events[i]
        if (
          invocationId != null &&
          next.invocationId != null &&
          next.invocationId !== invocationId
        ) {
          break
        }
        turnEvents.push(next)
        i += 1
      }

      if (turnEvents.length > 0) {
        const turn = extractPhotoFinderTurn(turnEvents)
        if (turn.message != null || turn.results != null) {
          messages.push({ role: 'agent', turn })
        }
      }
      continue
    }

    i += 1
  }

  return messages
}

function toAgentSessionSummary(raw: AdkSession): AgentSession {
  return {
    id: raw.id,
    title: sessionTitleFromState(raw.state),
    messages: [],
    createdAt: Math.round((raw.lastUpdateTime ?? Date.now() / 1000) * 1000),
  }
}

function toAgentSessionWithHistory(raw: AdkSession): AgentSession {
  const messages = eventsToChatMessages(raw.events ?? [])
  const firstUser = messages.find((m) => m.role === 'user')
  const firstUserText =
    firstUser && firstUser.role === 'user' ? firstUser.content : undefined

  return {
    id: raw.id,
    title: sessionTitleFromState(raw.state, firstUserText),
    messages,
    createdAt: Math.round((raw.lastUpdateTime ?? Date.now() / 1000) * 1000),
  }
}

/** GET /api/agents/sessions → slim AgentSession[] (messages empty). */
export async function listAgentSessions(): Promise<AgentSession[]> {
  const res = await fetch('/api/agents/sessions')
  if (!res.ok) await parseAgentError(res)
  const data = (await res.json()) as AdkListSessionsResponse
  const sessions = Array.isArray(data.sessions) ? data.sessions : []
  return sessions.map(toAgentSessionSummary)
}

/** GET /api/agents/sessions/{id} → slim AgentSession with history. */
export async function getAgentSession(
  sessionId: string,
): Promise<AgentSession> {
  const res = await fetch(`/api/agents/sessions/${encodeURIComponent(sessionId)}`)
  if (!res.ok) await parseAgentError(res)
  const raw = (await res.json()) as AdkSession
  return toAgentSessionWithHistory(raw)
}
