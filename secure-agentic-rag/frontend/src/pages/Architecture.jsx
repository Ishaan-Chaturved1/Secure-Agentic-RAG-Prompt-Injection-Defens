import React from 'react';
import { ArrowDown } from 'lucide-react';

export default function Architecture() {
  const steps = [
    {
      num: 1,
      title: 'User / External Client',
      desc: 'HTTP JSON Query payload sent via browser playground or REST API',
      file: 'POST /query',
      tagColor: 'text-slate-300 bg-slate-900 border-slate-750'
    },
    {
      num: 2,
      title: 'Layer 1: Input Guard',
      desc: 'Regex & heuristic scanner checks query string for known injection markers',
      file: 'injection_detector.py',
      tagColor: 'text-rose-300 bg-rose-950/50 border-rose-500/40 font-bold'
    },
    {
      num: 3,
      title: 'RAG Retrieval & Embeddings',
      desc: 'FAISS vector store semantic search over 17 knowledge base documents',
      file: 'retriever.py',
      tagColor: 'text-slate-300 bg-slate-900 border-slate-750'
    },
    {
      num: 4,
      title: 'Layer 2: Untrusted Document Boundary',
      desc: 'Wraps chunks in strict XML boundary tags; instructs model to treat as data, not commands',
      file: 'prompts.py',
      tagColor: 'text-orange-300 bg-orange-950/50 border-orange-500/40 font-bold'
    },
    {
      num: 5,
      title: 'LLM Inference Engine',
      desc: 'Deterministic Mock LLM or local Ollama (Llama 3.1:8b)',
      file: 'agent.py',
      tagColor: 'text-slate-300 bg-slate-900 border-slate-750'
    },
    {
      num: 6,
      title: 'Layer 3: Structured Schema Validation',
      desc: 'Extracts & parses JSON tool calls against strict Pydantic schemas',
      file: 'schemas.py',
      tagColor: 'text-amber-300 bg-amber-950/50 border-amber-500/40 font-bold'
    },
    {
      num: 7,
      title: 'Layer 4: Tool Authorization Policy',
      desc: 'Application allowlist: permits only search tools, blocks mock_delete/email/secret',
      file: 'tool_policy.py',
      tagColor: 'text-emerald-300 bg-emerald-950/50 border-emerald-500/40 font-bold'
    },
    {
      num: 8,
      title: 'Layer 5: Argument Validator',
      desc: 'Sanitizes tool arguments against path traversals, SQL injections, and metacharacters',
      file: 'validators.py',
      tagColor: 'text-sky-300 bg-sky-950/50 border-sky-500/40 font-bold'
    },
    {
      num: 9,
      title: 'Layer 6: Output Guardrail',
      desc: 'Scans response string for honeypot secrets or leaked tool prompts; redacts if found',
      file: 'output_guard.py',
      tagColor: 'text-purple-300 bg-purple-950/50 border-purple-500/40 font-bold'
    },
    {
      num: 10,
      title: 'Sanitized User Response & Audit Log',
      desc: 'Safe answer returned to client; decision persisted to audit log JSONL',
      file: 'audit.py',
      tagColor: 'text-cyan-300 bg-slate-900 border-cyan-500/30 font-bold'
    }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-8 font-mono">
      {/* Header */}
      <div className="pb-4 border-b border-cyan-950/40">
        <div className="text-cyan-400 text-xs font-bold tracking-widest flex items-center gap-2 mb-1">
          <span>//</span>
          <span>SYSTEM TOPOLOGY & FLOW</span>
        </div>
        <h1 className="text-3xl font-black text-white tracking-tight uppercase">System Architecture</h1>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed font-sans">
          Data flow diagram detailing how queries transition from user interfaces to sandboxed tools and sanitized responses.
        </p>
      </div>

      {/* Main End-to-End Pipeline Card */}
      <div className="panel p-6 sm:p-8 space-y-6 bg-[#060c18]/85 border-cyan-900/40 shadow-[0_0_25px_rgba(6,182,212,0.1)]">
        <div className="text-center space-y-1">
          <span className="text-[10px] uppercase tracking-widest text-cyan-400 font-bold">
            HIGH-LEVEL ARCHITECTURE MAP
          </span>
          <h2 className="text-lg font-bold text-white uppercase">Full Defense-in-Depth Pipeline</h2>
        </div>

        {/* Diagram Flow Nodes */}
        <div className="max-w-2xl mx-auto space-y-2.5 text-xs">
          {steps.map((step, idx) => (
            <React.Fragment key={step.num}>
              <div className="bg-slate-950 border border-slate-800 p-3.5 rounded flex items-center justify-between shadow-sm hover:border-cyan-500/50 transition-colors">
                <div className="flex items-center gap-3.5">
                  <span className="w-6 h-6 rounded bg-cyan-950/60 border border-cyan-500/40 text-cyan-300 flex items-center justify-center font-bold text-[11px]">
                    {step.num}
                  </span>
                  <div>
                    <div className="font-bold text-white text-xs">{step.title}</div>
                    <p className="text-[11px] text-slate-400 font-sans mt-0.5">{step.desc}</p>
                  </div>
                </div>
                <span className={`text-[10px] px-2.5 py-1 rounded border whitespace-nowrap ml-3 ${step.tagColor}`}>
                  {step.file}
                </span>
              </div>

              {idx < steps.length - 1 && (
                <div className="flex justify-center text-cyan-400">
                  <ArrowDown className="w-4 h-4" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}
