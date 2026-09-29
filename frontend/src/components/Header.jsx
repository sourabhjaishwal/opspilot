// Top navigation bar showing brand identity and authenticated user status
import { useAuth } from "../context/useAuth";

export default function Header() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="topbar">
      <div className="brand">
        <img 
          src="/monitoring.png" 
          alt="OpsPilot" 
          width="36" 
          height="36" 
          style={{ marginRight: '12px' }}
        />
        <div>
          <h1>OpsPilot</h1>
          <p className="subtitle">Microservice Incident Command Center</p>
        </div>
      </div>
      <div className="session-status">
        {isAuthenticated ? (
          <div className="user-session-group">
            <div className="user-badge">
              <span className="user-indicator-dot"></span>
              <span>
                <strong>{user?.username}</strong> ({user?.role})
              </span>
            </div>
            <button
              className="logout-button"
              onClick={logout}
              title="Log out of session"
            >
              Log out
            </button>
          </div>
        ) : (
          <span className="anon-pill">Not authenticated</span>
        )}
      </div>
    </header>
  );
}
