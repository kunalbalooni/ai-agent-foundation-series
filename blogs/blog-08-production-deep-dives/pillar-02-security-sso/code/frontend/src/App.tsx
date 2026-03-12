import React, { useState } from "react";
import { useMsal } from "@azure/msal-react";
import { AuthGuard } from "./components/AuthGuard";
import { useAgentApi } from "./api/agentApi";

function AgentChat() {
  const { accounts, instance } = useMsal();
  const { askQuestion } = useAgentApi();

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<
    { role: "user" | "agent"; text: string }[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const user = accounts[0];
  const sessionId = user?.localAccountId || "default";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    const q = question.trim();
    setQuestion("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setLoading(true);

    try {
      const answer = await askQuestion(q, sessionId);
      setMessages((prev) => [...prev, { role: "agent", text: answer }]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unexpected error";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = () => {
    instance.logoutRedirect({ postLogoutRedirectUri: window.location.origin });
  };

  return (
    <div style={styles.page}>
      {/* ── Header ── */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.logo}>🤖</span>
          <span style={styles.title}>AI Agent — SSO Demo</span>
        </div>
        <div style={styles.headerRight}>
          <span style={styles.userBadge}>
            {user?.name || user?.username || "Signed in"}
          </span>
          <button onClick={handleSignOut} style={styles.signOutBtn}>
            Sign out
          </button>
        </div>
      </header>

      {/* ── Auth info banner ── */}
      <div style={styles.infoBanner}>
        <strong>✅ Authenticated</strong> &nbsp;|&nbsp; Account:{" "}
        <code>{user?.username}</code> &nbsp;|&nbsp; Tenant:{" "}
        <code>{user?.tenantId}</code>
      </div>

      {/* ── Chat area ── */}
      <main style={styles.main}>
        <div style={styles.chatWindow}>
          {messages.length === 0 && (
            <div style={styles.emptyState}>
              Ask the agent a question to get started.
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              style={m.role === "user" ? styles.userMsg : styles.agentMsg}
            >
              <span style={styles.msgRole}>
                {m.role === "user" ? "You" : "Agent"}
              </span>
              <p style={styles.msgText}>{m.text}</p>
            </div>
          ))}
          {loading && (
            <div style={styles.agentMsg}>
              <span style={styles.msgRole}>Agent</span>
              <p style={{ ...styles.msgText, color: "#888" }}>Thinking…</p>
            </div>
          )}
          {error && (
            <div style={styles.errorMsg}>
              <strong>Error:</strong> {error}
            </div>
          )}
        </div>

        {/* ── Input ── */}
        <form onSubmit={handleSubmit} style={styles.inputRow}>
          <input
            style={styles.input}
            type="text"
            placeholder="Ask the agent…"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
          />
          <button type="submit" style={styles.sendBtn} disabled={loading || !question.trim()}>
            {loading ? "…" : "Send"}
          </button>
        </form>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthGuard>
      <AgentChat />
    </AuthGuard>
  );
}

// ── Inline styles (no extra dependencies needed) ──────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    fontFamily: "system-ui, -apple-system, sans-serif",
    background: "#f3f4f6",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 24px",
    height: "56px",
    background: "#0078d4",
    color: "#fff",
    boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
  },
  headerLeft: { display: "flex", alignItems: "center", gap: "10px" },
  logo: { fontSize: "22px" },
  title: { fontWeight: 600, fontSize: "16px" },
  headerRight: { display: "flex", alignItems: "center", gap: "12px" },
  userBadge: {
    fontSize: "13px",
    background: "rgba(255,255,255,0.2)",
    padding: "4px 10px",
    borderRadius: "12px",
  },
  signOutBtn: {
    background: "rgba(255,255,255,0.15)",
    border: "1px solid rgba(255,255,255,0.4)",
    color: "#fff",
    padding: "5px 14px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "13px",
  },
  infoBanner: {
    background: "#e6f4ea",
    borderBottom: "1px solid #b7dfba",
    padding: "8px 24px",
    fontSize: "13px",
    color: "#1a6b2a",
  },
  main: {
    display: "flex",
    flexDirection: "column",
    flex: 1,
    maxWidth: "760px",
    width: "100%",
    margin: "0 auto",
    padding: "24px 16px 16px",
    gap: "16px",
    overflow: "hidden",
  },
  chatWindow: {
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    paddingRight: "4px",
  },
  emptyState: {
    textAlign: "center",
    color: "#aaa",
    marginTop: "80px",
    fontSize: "15px",
  },
  userMsg: {
    alignSelf: "flex-end",
    background: "#0078d4",
    color: "#fff",
    borderRadius: "14px 14px 2px 14px",
    padding: "10px 16px",
    maxWidth: "75%",
  },
  agentMsg: {
    alignSelf: "flex-start",
    background: "#fff",
    color: "#1a1a1a",
    borderRadius: "14px 14px 14px 2px",
    padding: "10px 16px",
    maxWidth: "75%",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },
  msgRole: {
    display: "block",
    fontSize: "11px",
    fontWeight: 600,
    opacity: 0.6,
    marginBottom: "4px",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  msgText: { margin: 0, fontSize: "14px", lineHeight: "1.5" },
  errorMsg: {
    background: "#fde8e8",
    border: "1px solid #f5c2c2",
    color: "#b91c1c",
    borderRadius: "8px",
    padding: "10px 16px",
    fontSize: "13px",
  },
  inputRow: {
    display: "flex",
    gap: "8px",
  },
  input: {
    flex: 1,
    padding: "10px 14px",
    borderRadius: "8px",
    border: "1px solid #d1d5db",
    fontSize: "14px",
    outline: "none",
  },
  sendBtn: {
    padding: "10px 20px",
    background: "#0078d4",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontWeight: 600,
    fontSize: "14px",
    cursor: "pointer",
  },
};
