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
  listHydrated: boolean;
  historyLoadedIds: ReadonlySet<string>;
  setSessions: React.Dispatch<React.SetStateAction<AgentSession[]>>;
  setLocalMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  setListHydrated: React.Dispatch<React.SetStateAction<boolean>>;
  markHistoryLoaded: (id: string) => void;
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
  const [listHydrated, setListHydrated] = useState(false);
  const [historyLoadedIds, setHistoryLoadedIds] = useState<Set<string>>(
    () => new Set(),
  );

  const markHistoryLoaded = useCallback((id: string) => {
    setHistoryLoadedIds((prev) => {
      if (prev.has(id)) return prev;
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  }, []);

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
      listHydrated,
      historyLoadedIds,
      setSessions,
      setLocalMessages,
      setListHydrated,
      markHistoryLoaded,
      updateSessionMessages,
    }),
    [
      sessions,
      localMessages,
      listHydrated,
      historyLoadedIds,
      markHistoryLoaded,
      updateSessionMessages,
    ],
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
