import React from 'react';
import { ShieldCheck, Lock } from 'lucide-react';

export default function Footer({ setActivePage }) {
  return (
    <footer className="border-t border-cyan-950/40 bg-[#030712]/90 mt-16 font-mono">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <div className="p-1 rounded bg-cyan-950/80 border border-cyan-500/40 text-cyan-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <span className="font-bold text-xs tracking-wider uppercase text-white">
                Secure Agentic RAG Lab
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-md leading-relaxed font-sans">
              Applied AI security research lab demonstrating indirect prompt injection defenses, 
              tool authorization firewalls, and deterministic application guardrails.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-amber-300 font-mono bg-amber-950/20 border border-amber-500/30 px-3 py-1.5 rounded max-w-md">
              <Lock className="w-3.5 h-3.5 flex-shrink-0 text-amber-400" />
              <span>Safe Sandbox: Destructive actions and credentials are completely simulated.</span>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">
              Lab Navigation
            </h4>
            <ul className="space-y-2 text-xs text-slate-400 font-sans">
              <li>
                <button onClick={() => setActivePage('demo')} className="hover:text-cyan-400 transition-colors cursor-pointer">
                  Attack Playground
                </button>
              </li>
              <li>
                <button onClick={() => setActivePage('redteam')} className="hover:text-cyan-400 transition-colors cursor-pointer">
                  Red Team Suite (50)
                </button>
              </li>
              <li>
                <button onClick={() => setActivePage('security')} className="hover:text-cyan-400 transition-colors cursor-pointer">
                  6 Defense Layers
                </button>
              </li>
              <li>
                <button onClick={() => setActivePage('architecture')} className="hover:text-cyan-400 transition-colors cursor-pointer">
                  System Architecture
                </button>
              </li>
              <li>
                <button onClick={() => setActivePage('docs')} className="hover:text-cyan-400 transition-colors cursor-pointer">
                  Threat Model & API Reference
                </button>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">
              Specifications
            </h4>
            <div className="space-y-1.5 text-xs text-slate-400">
              <div className="flex justify-between border-b border-slate-900 pb-1">
                <span className="text-slate-500">Vector Index</span>
                <span className="text-slate-300 font-bold">FAISS-CPU</span>
              </div>
              <div className="flex justify-between border-b border-slate-900 pb-1">
                <span className="text-slate-500">Embeddings</span>
                <span className="text-slate-300 font-bold">all-MiniLM-L6-v2</span>
              </div>
              <div className="flex justify-between border-b border-slate-900 pb-1">
                <span className="text-slate-500">Backend</span>
                <span className="text-slate-300 font-bold">FastAPI</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Security Layers</span>
                <span className="text-emerald-400 font-bold">6 Active</span>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-900 mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500">
          <p>© 2026 Secure Agentic RAG Lab. Open-source defense research.</p>
          <div className="flex items-center gap-3 mt-2 sm:mt-0 text-slate-400">
            <span>Synthetic Honeypots</span>
            <span>•</span>
            <span>Safe Research Sandbox</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
