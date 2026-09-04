import React, { useState, useEffect, useCallback } from 'react';
import type { User } from '../types';
import { authApi } from '../api/endpoints';
import { AuthContext } from './AuthContextDef';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('workforce_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('workforce_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('workforce_token');
    localStorage.removeItem('workforce_refresh_token');
    localStorage.removeItem('workforce_user');
  }, []);

  const refreshUser = useCallback(async () => {
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
  }, [token, logout]);

  useEffect(() => {
    if (token) {
      refreshUser();
    } else {
      setIsLoading(false);
    }
  }, [token, refreshUser]);

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

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, refreshUser, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};
