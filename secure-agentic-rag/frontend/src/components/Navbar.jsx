import React, { useState, useEffect } from 'react';
import { Shield, Menu, X, User, LogOut, Lock } from 'lucide-react';
import { api } from '../services/api';

export default function Navbar({ activePage, setActivePage, currentUser, onOpenAuth, onLogout }) {
  const [healthy, setHealthy] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const check = () => api.checkHealth().then(() => setHealthy(true)).catch(() => setHealthy(false));
    check();
    const i = setInterval(check, 15000);
    return () => clearInterval(i);
  }, []);

  const nav = [
    { id: 'home', label: 'Overview' },
    { id: 'knowledge', label: 'My RAG' },
    { id: 'demo', label: 'Playground' },
    { id: 'redteam', label: 'Red Team' },
    { id: 'security', label: 'Layers' },
    { id: 'architecture', label: 'Architecture' },
    { id: 'docs', label: 'Docs' },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-cyan-950/40 bg-[#030712]/90 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-20">
        {/* Brand logo */}
        <div
          onClick={() => { setActivePage('home'); setMobileOpen(false); }}
          className="flex items-center gap-3.5 cursor-pointer group"
        >
          <div className="relative">
            <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-400 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.4)] group-hover:shadow-[0_0_25px_rgba(6,182,212,0.6)] transition-all">
              <Shield className="w-5 h-5 fill-cyan-400/20" />
            </div>
          </div>
          <div>
            <div className="font-extrabold text-base tracking-wider text-white font-mono uppercase">
              Secure Agentic RAG
            </div>
            <div className="text-[9px] font-mono tracking-widest text-slate-400 uppercase">
              Defense-In-Depth AI Gateway
            </div>
          </div>
        </div>

        {/* Center Nav */}
        <nav className="hidden md:flex items-center gap-6 lg:gap-8">
          {nav.map(n => (
            <button
              key={n.id}
              onClick={() => setActivePage(n.id)}
              className={`text-xs font-mono tracking-wider transition-all cursor-pointer relative py-2 ${
                activePage === n.id
                  ? 'text-cyan-400 font-bold border-b-2 border-cyan-400 shadow-[0_4px_12px_rgba(34,211,238,0.2)]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {n.label}
            </button>
          ))}
        </nav>

        {/* Right Status & Auth */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-full bg-slate-950/90 border border-slate-800 text-slate-300 shadow-inner">
            <span className={`w-2 h-2 rounded-full ${
              healthy === true 
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]' 
                : healthy === false 
                ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]' 
                : 'bg-amber-400'
            }`} />
            <span>{healthy === true ? 'Online' : healthy === false ? 'Offline' : 'Connecting...'}</span>
          </div>

          {currentUser ? (
            <div className="flex items-center gap-2 bg-slate-900 border border-cyan-500/30 rounded-lg p-1 text-xs font-mono">
              <div className="flex items-center gap-1.5 px-2 py-1 text-cyan-300">
                <User className="w-3.5 h-3.5" />
                <span className="font-bold">{currentUser.username}</span>
              </div>
              <button
                onClick={onLogout}
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded transition-colors cursor-pointer"
                title="Sign out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center gap-1.5 text-xs font-mono px-3.5 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500 hover:text-slate-950 transition-all cursor-pointer font-bold"
            >
              <Lock className="w-3 h-3" />
              <span>Sign In</span>
            </button>
          )}

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 text-slate-400 hover:text-white"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden px-6 py-4 border-t border-cyan-950/60 bg-[#030712] space-y-2">
          {nav.map(n => (
            <button
              key={n.id}
              onClick={() => { setActivePage(n.id); setMobileOpen(false); }}
              className={`block w-full text-left px-3 py-2 text-xs font-mono rounded ${
                activePage === n.id ? 'bg-cyan-950/40 text-cyan-400 border border-cyan-500/30' : 'text-slate-400'
              }`}
            >
              {n.label}
            </button>
          ))}
          {currentUser ? (
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
              <span className="text-xs font-mono text-cyan-300 font-bold">{currentUser.username}</span>
              <button
                onClick={() => { onLogout(); setMobileOpen(false); }}
                className="text-xs font-mono text-rose-400"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div className="pt-2 border-t border-slate-800">
              <button
                onClick={() => { onOpenAuth(); setMobileOpen(false); }}
                className="w-full py-2 text-xs font-mono bg-cyan-500 text-slate-950 font-bold rounded text-center"
              >
                Sign In
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
