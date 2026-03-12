import { useApiToken } from "../hooks/useApiToken";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export function useAgentApi() {
  const { getToken } = useApiToken();

  const askQuestion = async (
    question: string,
    sessionId: string
  ): Promise<string> => {
    // Acquire a fresh backend API token before each request
    // MSAL handles caching — this call is cheap when the token is still valid
    const token = await getToken();

    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`, // JWT token validated by FastAPI
      },
      body: JSON.stringify({ question, session_id: sessionId }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Request failed");
    }

    return (await response.json()).answer;
  };

  return { askQuestion };
}
