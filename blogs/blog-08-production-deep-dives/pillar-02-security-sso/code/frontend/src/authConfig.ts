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

// Scopes for the login request — Microsoft Graph only.
// User.Read is the minimum required for sign-in (AdminConsentRequired: No).
// Add "GroupMember.Read.All" here only if your use case requires real-time group
// membership resolution via Graph API (see Permission Configurations Reference in blog.md).
// If you add a scope here, it must also be registered in the portal under API permissions —
// mismatches cause AADSTS70011 and block login entirely.
// Reference: https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-single-page-app-react-sign-in
export const loginRequest: PopupRequest = {
  scopes: ["User.Read"],
};

// Scopes for acquiring a token to call the backend API
// Requested separately via acquireTokenSilent, not at login
export const apiRequest: PopupRequest = {
  scopes: [
    `api://${process.env.REACT_APP_AZURE_BACKEND_CLIENT_ID}/agent.query`,
  ],
};
