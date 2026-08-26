import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../types';
import { authApi } from '../api/endpoints';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User, refreshToken?: string) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('workforce_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('workforce_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const userData = await authApi.getMe();
      setUser(userData);
      localStorage.setItem('workforce_user', JSON.stringify(userData));
    } catch {
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      refreshUser();
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const login = (newToken: string, newUser: User, newRefreshToken?: string) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('workforce_token', newToken);
    localStorage.setItem('workforce_user', JSON.stringify(newUser));
    if (newRefreshToken) {
      localStorage.setItem('workforce_refresh_token', newRefreshToken);
    }
  };

  const updateUser = (updated: User) => {
    setUser(updated);
    localStorage.setItem('workforce_user', JSON.stringify(updated));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('workforce_token');
    localStorage.removeItem('workforce_refresh_token');
    localStorage.removeItem('workforce_user');
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, refreshUser, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
