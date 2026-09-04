import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  getAgentSession,
  listAgentSessions,
  sendPhotoFinderMessage,
  truncateTitle,
  type AgentSession,
  type ChatMessage,
} from "../api/agents";
import { useAgentSession } from "../components/agent/AgentSessionContext";
import { ChatWindow } from "../components/agent/ChatWindow";
import { SessionList } from "../components/agent/SessionList";

export function AgentPage() {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const {
    sessions,
    localMessages,
    listHydrated,
    historyLoadedIds,
    setSessions,
    setLocalMessages,
    setListHydrated,
    markHistoryLoaded,
    updateSessionMessages,
  } = useAgentSession();
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  const activeSession = useMemo(
    () => (sessionId ? sessions.find((s) => s.id === sessionId) : undefined),
    [sessions, sessionId],
  );

  const messages = activeSession?.messages ?? localMessages;

  useEffect(() => {
    if (listHydrated) return;

    let cancelled = false;
    ;(async () => {
      try {
        const remote = await listAgentSessions();
        if (cancelled) return;
        setSessions((prev) => {
          const byId = new Map(remote.map((s) => [s.id, s]));
          for (const local of prev) {
            const remoteSession = byId.get(local.id);
            if (!remoteSession || local.messages.length > 0) {
              byId.set(local.id, local);
            } else {
              byId.set(local.id, {
                ...remoteSession,
                title: local.title || remoteSession.title,
              });
            }
          }
          return Array.from(byId.values()).sort(
            (a, b) => b.createdAt - a.createdAt,
          );
        });
      } catch {
        // Sidebar stays empty / local-only until next reload.
      } finally {
        if (!cancelled) setListHydrated(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [listHydrated, setListHydrated, setSessions]);

  const sessionKnown = Boolean(
    sessionId && sessions.some((s) => s.id === sessionId),
  );
  const historyLoaded = Boolean(
    sessionId && historyLoadedIds.has(sessionId),
  );

  useEffect(() => {
    if (!sessionId || !listHydrated || !sessionKnown || historyLoaded) return;
    if (loading) return;

    let cancelled = false;
    setHistoryLoading(true);
    ;(async () => {
      try {
        const hydrated = await getAgentSession(sessionId);
        if (cancelled) return;
        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  title: hydrated.title,
                  messages: hydrated.messages,
                  createdAt: hydrated.createdAt,
                }
              : s,
          ),
        );
        markHistoryLoaded(sessionId);
      } catch {
        if (!cancelled) markHistoryLoaded(sessionId);
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [
    sessionId,
    listHydrated,
    sessionKnown,
    historyLoaded,
    loading,
    setSessions,
    markHistoryLoaded,
  ]);

  const handleNewChat = useCallback(() => {
    setLocalMessages([]);
    navigate("/agent");
  }, [navigate, setLocalMessages]);

  const handleSelectSession = useCallback(
    (id: string) => {
      setLocalMessages([]);
      navigate(`/agent/${id}`);
    },
    [navigate, setLocalMessages],
  );

  const handleSend = useCallback(
    async (text: string) => {
      const userMessage: ChatMessage = { role: "user", content: text };

      if (!sessionId) {
        const pendingMessages = [...localMessages, userMessage];
        setLocalMessages(pendingMessages);
        setLoading(true);
        try {
          const data = await sendPhotoFinderMessage(text);
          const newSession: AgentSession = {
            id: data.session,
            title: truncateTitle(text),
            messages: [
              ...pendingMessages,
              { role: "agent", turn: data.response },
            ],
            createdAt: Date.now(),
          };
          setSessions((prev) => [...prev, newSession]);
          markHistoryLoaded(data.session);
          setLocalMessages([]);
          navigate(`/agent/${data.session}`, { replace: true });
        } catch (err: unknown) {
          const msg =
            err instanceof Error ? err.message : "Failed to send message";
          setLocalMessages((prev) => [
            ...prev,
            { role: "error", content: msg },
          ]);
        } finally {
          setLoading(false);
        }
        return;
      }

      if (activeSession) {
        updateSessionMessages(sessionId, (prev) => [...prev, userMessage]);
      } else {
        setLocalMessages((prev) => [...prev, userMessage]);
      }

      const pendingMessages = activeSession
        ? undefined
        : [...localMessages, userMessage];

      setLoading(true);
      try {
        const data = await sendPhotoFinderMessage(text, sessionId);
        const agentMessage: ChatMessage = {
          role: "agent",
          turn: data.response,
        };

        if (activeSession) {
          updateSessionMessages(sessionId, (prev) => [...prev, agentMessage]);
          markHistoryLoaded(sessionId);
        } else if (pendingMessages) {
          const resumed: AgentSession = {
            id: data.session,
            title: truncateTitle(text),
            messages: [...pendingMessages, agentMessage],
            createdAt: Date.now(),
          };
          setSessions((prev) => {
            if (prev.some((s) => s.id === data.session)) return prev;
            return [...prev, resumed];
          });
          markHistoryLoaded(data.session);
          setLocalMessages([]);
        }
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "Failed to send message";
        const errorMessage: ChatMessage = { role: "error", content: msg };
        if (activeSession) {
          updateSessionMessages(sessionId, (prev) => [...prev, errorMessage]);
        } else {
          setLocalMessages((prev) => [...prev, errorMessage]);
        }
      } finally {
        setLoading(false);
      }
    },
    [
      sessionId,
      activeSession,
      localMessages,
      navigate,
      setSessions,
      setLocalMessages,
      updateSessionMessages,
      markHistoryLoaded,
    ],
  );

  return (
    <div className="flex h-full min-h-0 min-w-0 flex-col library:flex-row">
      <SessionList
        sessions={sessions}
        activeSessionId={sessionId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
      />
      <ChatWindow
        messages={messages}
        loading={loading || historyLoading}
        onSend={handleSend}
      />
    </div>
  );
}
