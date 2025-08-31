import React, { useState } from 'react';
import App from './App';
import DocsPage from './pages/docs';

const Router: React.FC = () => {
  const [currentPage, setCurrentPage] = useState('home');

  // Simple hash-based routing
  React.useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1);
      setCurrentPage(hash || 'home');
    };

    // Listen for hash changes
    window.addEventListener('hashchange', handleHashChange);
    
    // Set initial page based on current hash
    handleHashChange();

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigate = (page: string) => {
    window.location.hash = page;
    setCurrentPage(page);
  };

  // Pass navigation function to components
  const NavigationContext = React.createContext({ navigate });

  return (
    <NavigationContext.Provider value={{ navigate }}>
      {currentPage === 'docs' ? <DocsPage navigate={navigate} /> : <App navigate={navigate} />}
    </NavigationContext.Provider>
  );
};

export default Router;
