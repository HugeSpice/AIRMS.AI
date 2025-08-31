'use client';

import Navigation from '@/components/Navigation';
import { ReactNode } from 'react';

interface AppWrapperProps {
  children: ReactNode;
}

export default function AppWrapper({ children }: AppWrapperProps) {
  return (
    <>
      <Navigation />
      <div className="ml-0 md:ml-64 min-h-screen">
        {children}
      </div>
    </>
  );
}
