import React from 'react';
import { ShieldAlert, Terminal, AlertOctagon } from 'lucide-react';

export default function Docs() {
  const endpoints = [
    {
      method: 'POST',
      path: '/query',
      desc: 'Process a user query through the RAG pipeline in either baseline or hardened mode.',
      payload: '{ "query": "string", "mode": "hardened" | "baseline", "injected_documents": ["string"] }'
    },
    {
      method: 'GET',
      path: '/red-team/attacks',
      desc: 'Retrieve all 50 attack scenarios in the evaluation corpus.',
      payload: null
    },
    {
      method: 'POST',
      path: '/red-team/run-single',
      desc: 'Execute an attack simultaneously across Baseline and Hardened pipelines for side-by-side comparison.',
      payload: '{ "attack_id": "DIR-001" }'
    },
    {
      method: 'POST',
      path: '/red-team/run',
      desc: 'Run the complete 50-attack evaluation suite across specified configurations.',
      payload: null
    },
    {
      method: 'GET',
      path: '/red-team/results',
      desc: 'Fetch computed evaluation metrics from the latest benchmark run.',
      payload: null
    },
    {
      method: 'GET',
      path: '/audit/events',
      desc: 'Retrieve recent sanitized security decision events from the JSONL audit trail.',
      payload: null
    }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-8 font-mono">
      {/* Header */}
      <div className="pb-4 border-b border-cyan-950/40">
        <div className="text-cyan-400 text-xs font-bold tracking-widest flex items-center gap-2 mb-1">
          <span>//</span>
          <span>DOCUMENTATION & SPECIFICATIONS</span>
        </div>
        <h1 className="text-3xl font-black text-white tracking-tight uppercase">Threat Model & API Reference</h1>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed font-sans">
          Comprehensive threat vectors, security boundaries, honeypot secrets, and REST API endpoint documentation.
        </p>
      </div>

      {/* Threat Model */}
      <section className="panel p-6 sm:p-8 space-y-4 bg-[#060c18]/85 border-cyan-900/40 shadow-[0_0_20px_rgba(6,182,212,0.08)]">
        <h2 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span>Threat Model</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded bg-slate-950 border border-slate-800 space-y-2">
            <span className="font-bold text-rose-300 text-[11px] uppercase">Attacker Capabilities</span>
            <ul className="list-disc list-inside text-slate-300 space-y-1 text-[11px] font-sans">
              <li>Can influence or poison retrieved knowledge base documents</li>
              <li>Cannot modify core system prompts directly</li>
              <li>Cannot alter Python application code or policies</li>
            </ul>
          </div>

          <div className="p-4 rounded bg-slate-950 border border-slate-800 space-y-2">
            <span className="font-bold text-amber-300 text-[11px] uppercase">Attacker Objectives</span>
            <ul className="list-disc list-inside text-slate-300 space-y-1 text-[11px] font-sans">
              <li>Trigger unauthorized tool calls (mock_delete_file, mock_send_email)</li>
              <li>Extract synthetic secrets (RAG_FAKE_API_KEY)</li>
              <li>Escalate privileges via fake system headers</li>
              <li>Exfiltrate knowledge base data via HTTP/email</li>
            </ul>
          </div>
        </div>
      </section>

      {/* API Reference */}
      <section className="panel p-6 sm:p-8 space-y-4 bg-[#060c18]/85 border-cyan-900/40 shadow-[0_0_20px_rgba(6,182,212,0.08)]">
        <h2 className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span>REST API Endpoints</span>
        </h2>

        <div className="space-y-3 text-xs">
          {endpoints.map((ep, idx) => (
            <div key={idx} className="p-4 rounded bg-slate-950 border border-slate-800 space-y-1.5 hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  ep.method === 'POST' ? 'bg-cyan-950/70 text-cyan-400 border border-cyan-500/40' : 'bg-emerald-950/70 text-emerald-400 border border-emerald-500/40'
                }`}>
                  {ep.method}
                </span>
                <span className="text-white font-bold text-xs">{ep.path}</span>
              </div>
              <p className="text-slate-400 text-[11px] font-sans">{ep.desc}</p>
              {ep.payload && (
                <div className="text-[10px] text-slate-400 bg-slate-900/80 p-2.5 rounded border border-slate-800 font-mono">
                  Payload: {ep.payload}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Safe Public Sandbox Guarantee */}
      <section className="panel p-5 border-amber-500/30 bg-amber-950/15 space-y-2 text-xs">
        <div className="flex items-center gap-2 text-amber-400 font-bold text-xs">
          <AlertOctagon className="w-4 h-4 flex-shrink-0" />
          <span>Safe Public Sandbox Guarantee</span>
        </div>
        <p className="text-slate-300 leading-relaxed font-sans text-xs">
          This system uses deterministic mock tools (<code className="text-amber-300 font-bold bg-slate-900 px-1.5 py-0.5 rounded border border-amber-500/30">mock_delete_file</code>, <code className="text-amber-300 font-bold bg-slate-900 px-1.5 py-0.5 rounded border border-amber-500/30">mock_send_email</code>, <code className="text-amber-300 font-bold bg-slate-900 px-1.5 py-0.5 rounded border border-amber-500/30">mock_read_secret</code>) and synthetic honeypot credentials. No real files are ever modified, no emails are dispatched, and no cloud or database infrastructure can be impacted.
        </p>
      </section>
    </div>
  );
}
