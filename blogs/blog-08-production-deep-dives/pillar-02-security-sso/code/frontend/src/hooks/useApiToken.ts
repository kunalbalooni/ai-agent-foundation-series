import { useMsal } from "@azure/msal-react";
import { apiRequest } from "../authConfig";

// Custom hook that acquires a backend API token silently (from cache or via refresh token)
// Falls back to interactive popup if silent acquisition fails (e.g., token expired, consent needed)
export function useApiToken() {
  const { instance, accounts } = useMsal();

  const getToken = async (): Promise<string> => {
    if (accounts.length === 0) throw new Error("No authenticated account");

    try {
      // Try silent acquisition first — uses cached token or refresh token
      const result = await instance.acquireTokenSilent({
        ...apiRequest,
        account: accounts[0],
      });
      return result.accessToken;
    } catch {
      // Silent acquisition failed (interaction required) — show popup
      const result = await instance.acquireTokenPopup(apiRequest);
      return result.accessToken;
    }
  };

  return { getToken };
}
