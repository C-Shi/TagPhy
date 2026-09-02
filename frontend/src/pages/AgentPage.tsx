import { useCallback, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
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
    setSessions,
    setLocalMessages,
    updateSessionMessages,
  } = useAgentSession();
  const [loading, setLoading] = useState(false);

  const activeSession = useMemo(
    () => (sessionId ? sessions.find((s) => s.id === sessionId) : undefined),
    [sessions, sessionId],
  );

  const messages = activeSession?.messages ?? localMessages;

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
      <ChatWindow messages={messages} loading={loading} onSend={handleSend} />
    </div>
  );
}
