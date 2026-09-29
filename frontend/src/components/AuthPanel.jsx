// Authentication panel providing user login and registration forms
import { useState } from "react";
import { login as loginApi, register as registerApi } from "../api/client";

export default function AuthPanel({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    username: "",
    password: "",
    role: "user",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notice, setNotice] = useState(null); // { message: string, type: 'error' | 'success' }

  // Handle credentials form submission
  async function handleSubmit(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setNotice(null);

    try {
      if (mode === "login") {
        const session = await loginApi({
          username: form.username,
          password: form.password,
        });
        onAuthenticated(session);
      } else {
        const session = await registerApi(form);
        setNotice({
          message: "Account registered successfully! Logging you in...",
          type: "success",
        });
        onAuthenticated(session);
      }
    } catch (err) {
      setNotice({
        message: err.message || "Authentication failed. Please try again.",
        type: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleModeChange(nextMode) {
    setMode(nextMode);
    setNotice(null);
  }

  return (
    <div className="auth-card">
      <div className="auth-tabs">
        <button
          type="button"
          className={mode === "login" ? "tab-active" : ""}
          onClick={() => handleModeChange("login")}
        >
          Sign In
        </button>
        <button
          type="button"
          className={mode === "register" ? "tab-active" : ""}
          onClick={() => handleModeChange("register")}
        >
          Create Account
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        {notice && (
          <div className={`auth-notice ${notice.type}`} role="alert">
            {notice.message}
          </div>
        )}

        <label>
          Username
          <input
            required
            autoComplete="username"
            value={form.username}
            onChange={(event) =>
              setForm({ ...form, username: event.target.value })
            }
            placeholder="admin"
          />
        </label>

        <label>
          Password
          <input
            required
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            value={form.password}
            onChange={(event) =>
              setForm({ ...form, password: event.target.value })
            }
            placeholder="••••••••"
          />
        </label>

        {mode === "register" && (
          <label>
            Role
            <select
              value={form.role}
              onChange={(event) =>
                setForm({ ...form, role: event.target.value })
              }
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </label>
        )}

        <button
          type="submit"
          className="primary-button"
          disabled={isSubmitting}
        >
          {isSubmitting
            ? "Processing..."
            : mode === "login"
              ? "Sign In"
              : "Register Account"}
        </button>
      </form>
    </div>
  );
}
