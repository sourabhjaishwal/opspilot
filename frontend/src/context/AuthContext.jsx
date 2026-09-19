import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { logout } from "../api/client";

const AuthContext = createContext(null);

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
      login: (session) => {
        setToken(session.access_token);
        setUser(session.user);
      },
      logout: async () => {
        try {
          await logout();
        } catch {
          // Ignore backend logout errors and clear the session locally.
        }
        setToken("");
        setUser(null);
      },
    }),
    [token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
