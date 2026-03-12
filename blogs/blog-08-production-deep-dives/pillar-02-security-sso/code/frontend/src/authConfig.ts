import { Configuration, PopupRequest } from "@azure/msal-browser";

// MSAL configuration — loaded from environment variables at runtime
// Never hardcode client IDs or tenant IDs in source code
export const msalConfig: Configuration = {
  auth: {
    clientId: process.env.REACT_APP_AZURE_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.REACT_APP_AZURE_TENANT_ID}`,
    redirectUri: window.location.origin, // Matches the redirect URI in app registration
  },
  cache: {
    cacheLocation: "sessionStorage", // sessionStorage: cleared on tab close (more secure)
    storeAuthStateInCookie: false, // Set true only if IE11 support is required
  },
};

// Scopes for the login request — Microsoft Graph only
// Do NOT include backend API scopes here
export const loginRequest: PopupRequest = {
  scopes: ["User.Read", "GroupMember.Read.All"],
};

// Scopes for acquiring a token to call the backend API
// Requested separately via acquireTokenSilent, not at login
export const apiRequest: PopupRequest = {
  scopes: [
    `api://${process.env.REACT_APP_AZURE_BACKEND_CLIENT_ID}/agent.query`,
  ],
};
