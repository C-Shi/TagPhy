import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { AgentSession, ChatMessage } from "../../api/agents";

type AgentSessionContextValue = {
  sessions: AgentSession[];
  localMessages: ChatMessage[];
  setSessions: React.Dispatch<React.SetStateAction<AgentSession[]>>;
  setLocalMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  updateSessionMessages: (
    id: string,
    updater: (prev: ChatMessage[]) => ChatMessage[],
  ) => void;
};

const AgentSessionContext = createContext<AgentSessionContextValue | null>(
  null,
);

export function AgentSessionProvider({ children }: { children: ReactNode }) {
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);

  const updateSessionMessages = useCallback(
    (id: string, updater: (prev: ChatMessage[]) => ChatMessage[]) => {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === id ? { ...s, messages: updater(s.messages) } : s,
        ),
      );
    },
    [],
  );

  const value = useMemo(
    () => ({
      sessions,
      localMessages,
      setSessions,
      setLocalMessages,
      updateSessionMessages,
    }),
    [sessions, localMessages, updateSessionMessages],
  );

  return (
    <AgentSessionContext.Provider value={value}>
      {children}
    </AgentSessionContext.Provider>
  );
}

export function useAgentSession() {
  const ctx = useContext(AgentSessionContext);
  if (!ctx) {
    throw new Error("useAgentSession must be used within AgentSessionProvider");
  }
  return ctx;
}
