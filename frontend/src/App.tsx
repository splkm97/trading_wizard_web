import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { Navigation } from './components/common/Navigation';
import { Disclaimer } from './components/common/Disclaimer';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import TradePage from './pages/TradePage';
import { HistoryPage } from './pages/HistoryPage';
import { BacktestPage } from './pages/BacktestPage';
import { SettingsPage } from './pages/SettingsPage';
import { SimulationPage } from './pages/SimulationPage';
import { ContrarianPage } from './pages/ContrarianPage';
import { GuidePage, GUIDE_SEEN_KEY } from './pages/GuidePage';

function FirstVisitRedirect() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    const guideSeen = localStorage.getItem(GUIDE_SEEN_KEY);
    const isGuidePage = location.pathname === '/guide';
    const isLoginPage = location.pathname === '/login';

    if (isAuthenticated && !guideSeen && !isGuidePage && !isLoginPage) {
      navigate('/guide', { replace: true });
    }
  }, [isAuthenticated, isLoading, location.pathname, navigate]);

  return null;
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
          <Disclaimer />
          <Navigation />
          <FirstVisitRedirect />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/trade"
            element={
              <ProtectedRoute>
                <TradePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/backtest"
            element={
              <ProtectedRoute>
                <BacktestPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/simulation"
            element={
              <ProtectedRoute>
                <SimulationPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/simulation/:sessionId"
            element={
              <ProtectedRoute>
                <SimulationPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/contrarian"
            element={
              <ProtectedRoute>
                <ContrarianPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/guide"
            element={
              <ProtectedRoute>
                <GuidePage />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
