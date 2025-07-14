import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  username: string;
  student_id: string;
  egov_password: string;
}

interface AuthContextType {
  user: User | null;
  sessionId: string | null;
  login: (sessionId: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    // Check for existing session on mount
    const storedSessionId = localStorage.getItem('sessionId');
    const storedUser = localStorage.getItem('user');
    
    if (storedSessionId && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setSessionId(storedSessionId);
        setUser(parsedUser);
      } catch (error) {
        // Clear invalid data
        localStorage.removeItem('sessionId');
        localStorage.removeItem('user');
      }
    }
  }, []);

  const login = (newSessionId: string, newUser: User) => {
    setSessionId(newSessionId);
    setUser(newUser);
    localStorage.setItem('sessionId', newSessionId);
    localStorage.setItem('user', JSON.stringify(newUser));
  };

  const logout = async () => {
    // Call logout API if session exists
    if (sessionId) {
      try {
        await fetch('http://localhost:8093/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${sessionId}`,
          },
        });
      } catch (error) {
        console.error('Logout API call failed:', error);
      }
    }
    
    // Clear chat memory through WebSocket
    try {
      const ws = new WebSocket("ws://localhost:8092");
      ws.onopen = () => {
        ws.send("LOGOUT");
        ws.close();
      };
    } catch (error) {
      console.error('Failed to clear chat memory:', error);
    }
    
    setSessionId(null);
    setUser(null);
    localStorage.removeItem('sessionId');
    localStorage.removeItem('user');
  };

  const value: AuthContextType = {
    user,
    sessionId,
    login,
    logout,
    isAuthenticated: !!(user && sessionId),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
