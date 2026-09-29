// Authentication page layout containing promotional hero and auth form panel
import AuthPanel from "../components/AuthPanel";
import { useAuth } from "../context/useAuth";

export default function AuthPage() {
  const { login } = useAuth();

  return (
    <div className="auth-layout">
      <div className="auth-hero">
        <span className="eyebrow">Enterprise Reliability</span>
        <h2>Unified command center for cloud-native services.</h2>
        <p>
          Monitor microservice health in real-time, declare incidents
          with high-fidelity telemetry, and coordinate root-cause investigation
          across engineering teams.
        </p>
      </div>
      <AuthPanel onAuthenticated={login} />
    </div>
  );
}
