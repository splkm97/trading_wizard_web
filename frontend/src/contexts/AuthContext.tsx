import { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import { api } from '../services/api';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, fingerprint: string) => void;
  logout: () => void;
  resetActivityTimer: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = 'trading_wizard_token';
const FINGERPRINT_KEY = 'trading_wizard_fingerprint';
const LAST_ACTIVITY_KEY = 'trading_wizard_last_activity';
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearSession = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(FINGERPRINT_KEY);
    localStorage.removeItem(LAST_ACTIVITY_KEY);
    api.setToken(null);
    setUser(null);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, []);

  const checkSessionTimeout = useCallback(() => {
    const lastActivity = localStorage.getItem(LAST_ACTIVITY_KEY);
    if (lastActivity) {
      const elapsed = Date.now() - parseInt(lastActivity, 10);
      if (elapsed > SESSION_TIMEOUT_MS) {
        console.log('Session timeout - logging out');
        clearSession();
        return true;
      }
    }
    return false;
  }, [clearSession]);

  const userRef = useRef<User | null>(null);
  userRef.current = user;

  const resetActivityTimer = useCallback(() => {
    localStorage.setItem(LAST_ACTIVITY_KEY, Date.now().toString());

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      if (userRef.current) {
        console.log('Session timeout due to inactivity');
        clearSession();
      }
    }, SESSION_TIMEOUT_MS);
  }, [clearSession]);

  useEffect(() => {
    // Check for existing token on mount
    const token = localStorage.getItem(TOKEN_KEY);
    const fingerprint = localStorage.getItem(FINGERPRINT_KEY);

    if (token && fingerprint) {
      // Check if session has timed out
      if (!checkSessionTimeout()) {
        api.setToken(token);
        setUser({
          id: '',
          fingerprint,
          nickname: null,
          created_at: '',
          last_login_at: null,
        });
        resetActivityTimer();
      }
    }
    setIsLoading(false);
  }, [checkSessionTimeout, resetActivityTimer]);

  // Track user activity
  useEffect(() => {
    if (!user) return;

    const handleActivity = () => {
      resetActivityTimer();
    };

    // Listen to various user activity events
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    events.forEach((event) => {
      window.addEventListener(event, handleActivity);
    });

    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity);
      });
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [user, resetActivityTimer]);

  const login = (token: string, fingerprint: string) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(FINGERPRINT_KEY, fingerprint);
    api.setToken(token);
    setUser({
      id: '',
      fingerprint,
      nickname: null,
      created_at: '',
      last_login_at: null,
    });
    resetActivityTimer();
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout', {});
    } catch {
      // Ignore errors on logout
    } finally {
      clearSession();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        resetActivityTimer,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
