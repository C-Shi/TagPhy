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
