import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Demo from './pages/Demo';
import RedTeam from './pages/RedTeam';
import Security from './pages/Security';
import Architecture from './pages/Architecture';
import Docs from './pages/Docs';
import KnowledgeBase from './pages/KnowledgeBase';
import AuthModal from './components/AuthModal';
import { api, getStoredUser, clearStoredAuth } from './services/api';

export default function App() {
  const [activePage, setActivePage] = useState('home');
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const [authModalOpen, setAuthModalOpen] = useState(false);

  useEffect(() => {
    // Verify session on app load
    if (currentUser) {
      api.getMe()
        .then((res) => {
          if (res?.user) setCurrentUser(res.user);
        })
        .catch(() => {
          clearStoredAuth();
          setCurrentUser(null);
        });
    }
  }, []);

  const handleLogout = async () => {
    await api.logout();
    setCurrentUser(null);
    if (activePage === 'knowledge') {
      setActivePage('home');
    }
  };

  const renderPage = () => {
    switch (activePage) {
      case 'home':
        return <Home setActivePage={setActivePage} />;
      case 'knowledge':
        return (
          <KnowledgeBase
            currentUser={currentUser}
            setCurrentUser={setCurrentUser}
          />
        );
      case 'demo':
        return <Demo />;
      case 'redteam':
        return <RedTeam />;
      case 'security':
        return <Security />;
      case 'architecture':
        return <Architecture />;
      case 'docs':
        return <Docs />;
      default:
        return <Home setActivePage={setActivePage} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#030712] text-slate-100 cyber-grid relative selection:bg-cyan-500 selection:text-black">
      <Navbar
        activePage={activePage}
        setActivePage={setActivePage}
        currentUser={currentUser}
        onOpenAuth={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
      />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {renderPage()}
      </main>
      <Footer setActivePage={setActivePage} />

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={(user) => setCurrentUser(user)}
      />
    </div>
  );
}
