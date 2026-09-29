// Authentication state provider managing user session and persistent tokens
import { useEffect, useMemo, useState } from "react";
import { AuthContext } from "./authContext";

// Safely retrieve cached user from browser storage
function readStoredUser() {
  try {
    const storedUser = localStorage.getItem("opspilot_user");
    return storedUser ? JSON.parse(storedUser) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser);
  const [token, setToken] = useState(
    () => localStorage.getItem("opspilot_token") || "",
  );

  // Sync state changes with localStorage
  useEffect(() => {
    if (user) {
      localStorage.setItem("opspilot_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("opspilot_user");
    }
  }, [user]);

  useEffect(() => {
    if (token) {
      localStorage.setItem("opspilot_token", token);
    } else {
      localStorage.removeItem("opspilot_token");
    }
  }, [token]);

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      // Synchronously write to localStorage on login to avoid auth race conditions
      login: (session) => {
        if (session.access_token) {
          localStorage.setItem("opspilot_token", session.access_token);
        }
        if (session.user) {
          localStorage.setItem("opspilot_user", JSON.stringify(session.user));
        }
        setToken(session.access_token);
        setUser(session.user);
      },
      // Clear credentials on logout
      logout: () => {
        localStorage.removeItem("opspilot_token");
        localStorage.removeItem("opspilot_user");
        setToken("");
        setUser(null);
      },
    }),
    [token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
