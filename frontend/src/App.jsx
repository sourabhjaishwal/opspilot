// OpsPilot root application component managing top-level page routing and layout structure
import Header from "./components/Header";
import Footer from "./components/Footer";
import AuthPage from "./pages/AuthPage";
import DashboardPage from "./pages/DashboardPage";
import { useAuth } from "./context/useAuth";
import "./styles.scss";

export default function App() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="app-shell">
      <Header />
      <main className={isAuthenticated ? "" : "auth-main"}>
        {isAuthenticated ? <DashboardPage /> : <AuthPage />}
      </main>
      {isAuthenticated && <Footer />}
    </div>
  );
}
