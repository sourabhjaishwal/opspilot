import { useState } from "react";
import { login, register } from "../api/client";

function AuthPanel({ onAuthenticated, onError }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    username: "",
    password: "",
    role: "user",
  });
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState("");

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    setNotice("");
    onError("");
    try {
      const session = await (mode === "login" ? login(form) : register(form));
      setNotice(
        mode === "login"
          ? "Signed in successfully."
          : "Account created successfully.",
      );
      onAuthenticated(session);
    } catch (error) {
      const message = error.message || "Authentication failed.";
      setNotice(message);
      onError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="auth-panel panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Operator access</p>
          <h3>
            {mode === "login" ? "Sign in to OpsPilot" : "Create an account"}
          </h3>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login" ? "Register" : "Sign in"}
        </button>
      </div>
      <form onSubmit={submit}>
        <label>
          Username
          <input
            required
            minLength="3"
            value={form.username}
            onChange={(event) =>
              setForm({ ...form, username: event.target.value })
            }
          />
        </label>
        <label>
          Password
          <input
            required
            minLength="8"
            type="password"
            value={form.password}
            onChange={(event) =>
              setForm({ ...form, password: event.target.value })
            }
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
        {notice && <div className="auth-notice">{notice}</div>}
        <button className="primary-button" disabled={submitting} type="submit">
          {submitting
            ? "Working..."
            : mode === "login"
              ? "Sign in"
              : "Create account"}
        </button>
      </form>
    </section>
  );
}

export default AuthPanel;
