'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiService from '@/services/api';

// Update interfaces to match backend models
interface ApiKey {
  id: string;
  user_id: string;
  key_name: string;
  key_prefix: string;
  permissions: string[];
  usage_limit?: number;
  usage_count: number;
  is_active: boolean;
  expires_at?: string;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
}

interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

interface ApiKeyCreateResponse {
  key_data: ApiKey;
  api_key: string; // The actual key - only shown once
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string, fullName: string) => Promise<boolean>;
  logout: () => void;
  generateApiKey: (name: string) => Promise<ApiKeyCreateResponse | null>;
  revokeApiKey: (keyId: string) => Promise<boolean>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('authToken');
      if (token) {
        const userData = await apiService.getCurrentUser();
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('authToken');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      console.log('Login: Starting login process...');
      const response: LoginResponse = await apiService.login(email, password);
      
      console.log('Login: Success, setting user and token...');
      localStorage.setItem('authToken', response.access_token);
      setUser(response.user);
      console.log('Login: User set, isAuthenticated should be:', !!response.user);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const response = await apiService.register(email, password, fullName);
      return true;
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
  };

  const generateApiKey = async (name: string): Promise<ApiKeyCreateResponse | null> => {
    try {
      const response = await apiService.generateApiKey(name);
      await refreshUser();
      return response;
    } catch (error) {
      console.error('Failed to generate API key:', error);
      return null;
    }
  };

  const revokeApiKey = async (keyId: string): Promise<boolean> => {
    try {
      await apiService.revokeApiKey(keyId);
      await refreshUser();
      return true;
    } catch (error) {
      console.error('Failed to revoke API key:', error);
      return false;
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await apiService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    generateApiKey,
    revokeApiKey,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
