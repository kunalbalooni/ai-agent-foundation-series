import React from "react";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import { InteractionStatus } from "@azure/msal-browser";
import { loginRequest } from "../authConfig";

interface AuthGuardProps {
  children: React.ReactNode;
}

// Wraps any component that requires authentication.
// Redirects unauthenticated users to the Microsoft login page.
//
// IMPORTANT: loginRedirect must only be called when inProgress === InteractionStatus.None.
// After Azure AD redirects back to the app with an authorisation code, MSAL needs a brief
// window to process that redirect and exchange the code for tokens. During this window,
// useIsAuthenticated() still returns false. Calling loginRedirect() during this processing
// window causes an infinite redirect loop: MSAL never finishes handling the first redirect
// because a new one is immediately triggered.
//
// Checking inProgress prevents the redirect from firing while MSAL is mid-interaction
// (InteractionStatus.HandleRedirect), ensuring MSAL completes token acquisition before
// AuthGuard evaluates authentication state.
//
// NOTE: This guard is a secondary safety net. The primary fix for the redirect loop is in
// index.tsx — awaiting msalInstance.initialize() before rendering. Together, these two
// guards fully prevent the infinite redirect.
export function AuthGuard({ children }: AuthGuardProps) {
  const isAuthenticated = useIsAuthenticated();
  const { instance, inProgress } = useMsal();

  // MSAL is still processing a redirect (e.g. handling the auth code returned by Azure AD).
  // Do NOT trigger another loginRedirect — wait for MSAL to finish and update auth state.
  if (inProgress !== InteractionStatus.None) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner} />
        <p>Signing you in…</p>
      </div>
    );
  }

  // MSAL is idle and user is not authenticated — safe to initiate login redirect.
  if (!isAuthenticated) {
    instance.loginRedirect(loginRequest);
    return (
      <div style={styles.loading}>
        <p>Redirecting to sign-in…</p>
      </div>
    );
  }

  return <>{children}</>;
}

const styles: Record<string, React.CSSProperties> = {
  loading: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100vh",
    fontFamily: "system-ui, sans-serif",
    color: "#555",
    gap: "12px",
  },
  spinner: {
    width: "40px",
    height: "40px",
    border: "4px solid #e0e0e0",
    borderTop: "4px solid #0078d4",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
};
