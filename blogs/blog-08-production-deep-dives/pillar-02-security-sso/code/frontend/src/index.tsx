import React from "react";
import ReactDOM from "react-dom/client";
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { msalConfig } from "./authConfig";
import App from "./App";

// Create the MSAL instance once at app startup.
const msalInstance = new PublicClientApplication(msalConfig);

// ─── BUG FIX ────────────────────────────────────────────────────────────────
// The blog's original code renders <MsalProvider> immediately after constructing
// the PublicClientApplication, without ever calling msalInstance.initialize().
//
// In MSAL Browser v3+, initialize() is REQUIRED before the instance is passed
// to MsalProvider. It is an async operation that:
//   1. Restores any cached account state from sessionStorage.
//   2. Processes the redirect response in the URL (the ?code=... returned by
//      Azure AD after the user authenticates).
//   3. Exchanges the authorisation code for tokens and writes them to cache.
//
// Without initialize(), step 2 never happens. When Azure AD redirects back to
// the app, MSAL never processes the auth code, so useIsAuthenticated() stays
// false. AuthGuard immediately calls loginRedirect() again — and the user is
// sent straight back to the Microsoft login page in an infinite loop.
//
// The fix: await initialize() before rendering. This guarantees that MSAL has
// fully handled the redirect and populated the account cache before AuthGuard
// (or any other component) evaluates authentication state.
// ────────────────────────────────────────────────────────────────────────────
msalInstance.initialize().then(() => {
  const root = ReactDOM.createRoot(
    document.getElementById("root") as HTMLElement
  );
  root.render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </React.StrictMode>
  );
});
