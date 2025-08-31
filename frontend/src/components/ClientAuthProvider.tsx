'use client';

import { AuthProvider } from '@/contexts/AuthContext';

interface ClientAuthProviderProps {
  children: React.ReactNode;
}

export default function ClientAuthProvider({ children }: ClientAuthProviderProps) {
  // Render immediately without waiting for client-side hydration
  return <AuthProvider>{children}</AuthProvider>;
}
