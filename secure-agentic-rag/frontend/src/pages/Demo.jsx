import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, ShieldAlert, Play, RefreshCw, 
  Copy, Check, ChevronDown, Zap
} from 'lucide-react';
import { api } from '../services/api';

export default function Demo() {
  const [tab, setTab] = useState('attack');
  const [mode, setMode] = useState('hardened');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Attack state
  const [attacks, setAttacks] = useState([]);
  const [selected, setSelected] = useState(null);
  const [filter, setFilter] = useState('');
  const [category, setCategory] = useState('ALL');
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(null);

  // Query state
  const [query, setQuery] = useState('What is the employee leave policy?');
  const [queryResult, setQueryResult] = useState(null);

  useEffect(() => {
    api.getAttacks().then(data => {
      setAttacks(data);
      if (data.length) setSelected(data.find(a => a.id === 'DIR-002') || data[0]);
    }).catch(() => {});
  }, []);

  const runAttack = async () => {
    if (!selected) return;
    setLoading(true); setError(null);
    try {
      setResult(await api.executeAttack(selected.id, mode));
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const runQuery = async (q) => {
    const text = q || query;
    if (!text.trim()) return;
    setLoading(true); setError(null);
    try {
      setQueryResult(await api.queryAgent({ query: text, mode }));
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const copy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 1500);
  };

  const categories = ['ALL', ...new Set(attacks.map(a => a.category))];
  const filtered = attacks.filter(a => {
    const s = filter.toLowerCase();
    const matchText = a.id.toLowerCase().includes(s) || a.description.toLowerCase().includes(s);
    const matchCat = category === 'ALL' || a.category === category;
    return matchText && matchCat;
  });

  return (
    <div className="py-8 space-y-6">
      {/* Header row */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <div className="text-cyan-400 font-mono text-xs font-bold tracking-widest flex items-center gap-2 mb-1">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
            <span>// ATTACK PLAYGROUND</span>
          </div>
          <h1 className="text-3xl font-black text-white font-mono tracking-tight uppercase">
            Security Playground
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Test adversarial attacks against the RAG agent or run benign knowledge-base queries.
          </p>
        </div>

        {/* Mode toggle with vivid red & green accents */}
        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-slate-950/90 border border-slate-800 font-mono shadow-sm">
          <button
            onClick={() => setMode('baseline')}
            className={`px-3.5 py-1.5 rounded text-xs font-bold transition-all cursor-pointer ${
              mode === 'baseline' 
                ? 'bg-rose-500/25 text-rose-300 border border-rose-500/50 shadow-[0_0_15px_rgba(244,63,94,0.35)] scale-105' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Baseline
          </button>
          <button
            onClick={() => setMode('hardened')}
            className={`px-3.5 py-1.5 rounded text-xs font-bold transition-all cursor-pointer ${
              mode === 'hardened' 
                ? 'bg-emerald-500/25 text-emerald-300 border border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.35)] scale-105' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Hardened
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-6 border-b border-cyan-950/40 text-xs font-mono">
        {[
          { id: 'attack', label: 'ATTACK SIMULATION' },
          { id: 'query', label: 'BENIGN RAG QUERY' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`pb-2.5 font-bold cursor-pointer transition-all duration-200 ${
              tab === t.id
                ? 'text-cyan-400 border-b-2 border-cyan-400 shadow-[0_4px_12px_rgba(34,211,238,0.25)]'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="text-xs font-mono text-rose-300 bg-rose-950/40 border border-rose-500/40 rounded-lg px-4 py-3 shadow-[0_0_15px_rgba(244,63,94,0.2)] animate-shake">
          {error}
        </div>
      )}

      {/* ── ATTACK TAB ── */}
      {tab === 'attack' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Sidebar: attack list */}
          <div className="lg:col-span-4 space-y-3 font-mono">
            <div className="panel p-4 space-y-3 bg-[#060c18]/85 border-cyan-900/40">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-bold text-white uppercase text-[11px]">Attacks</span>
                <span className="bg-slate-900 px-2 py-0.5 rounded text-[11px] text-cyan-400 border border-slate-800">{filtered.length} / {attacks.length}</span>
              </div>

              <input
                type="text"
                placeholder="Filter ID or keyword..."
                value={filter}
                onChange={e => setFilter(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 font-mono transition-colors"
              />

              <div className="relative">
                <select
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-cyan-500 font-mono appearance-none cursor-pointer transition-colors"
                >
                  {categories.map(c => (
                    <option key={c} value={c}>{c === 'ALL' ? 'All categories' : c.replace(/_/g, ' ')}</option>
                  ))}
                </select>
                <ChevronDown className="w-3.5 h-3.5 absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
              </div>

              <div className="space-y-1 max-h-[520px] overflow-y-auto pr-1">
                {filtered.map(atk => (
                  <button
                    key={atk.id}
                    onClick={() => { setSelected(atk); setResult(null); }}
                    className={`w-full text-left px-3 py-2.5 rounded text-xs cursor-pointer transition-all duration-150 border ${
                      selected?.id === atk.id
                        ? 'bg-cyan-950/60 border-cyan-400 text-white shadow-[0_0_15px_rgba(6,182,212,0.25)] translate-x-1'
                        : 'border-transparent text-slate-400 hover:bg-slate-900/60 hover:text-slate-200 hover:translate-x-0.5'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[11px] font-bold text-cyan-400">{atk.id}</span>
                      <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold uppercase transition-transform hover:scale-105 ${
                        atk.severity === 'critical' 
                          ? 'text-rose-400 bg-rose-950/50 border border-rose-500/40 shadow-[0_0_8px_rgba(244,63,94,0.3)]' 
                          : 'text-amber-400 bg-amber-950/50 border border-amber-500/40 shadow-[0_0_8px_rgba(245,158,11,0.3)]'
                      }`}>
                        {atk.severity}
                      </span>
                    </div>
                    <p className="text-[11px] mt-1 text-slate-300 truncate font-sans">{atk.description}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main content */}
          <div className="lg:col-span-8 space-y-5">
            {selected ? (
              <>
                {/* Attack info card */}
                <div className="panel p-6 space-y-5 bg-[#060c18]/85 border-cyan-900/40">
                  {/* Header */}
                  <div className="flex flex-wrap items-start justify-between gap-2 pb-4 border-b border-slate-800/80 font-mono">
                    <div>
                      <div className="flex items-center gap-2.5">
                        <h2 className="text-xl font-black text-white">{selected.id}</h2>
                        <span className="text-[11px] text-cyan-300 font-bold px-2.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.2)]">
                          {selected.category.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 mt-1 font-sans">{selected.description}</p>
                    </div>
                    <div className="text-right text-[11px] text-slate-400 space-y-0.5">
                      <div>Target Tool: <span className="text-amber-400 font-bold">{selected.target_tool || '—'}</span></div>
                      {selected.target_secret && (
                        <div>Secret: <span className="text-rose-400 font-bold">{selected.target_secret}</span></div>
                      )}
                    </div>
                  </div>

                  {/* Two-column: Query + Payload */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono">
                    {/* User query */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span className="font-bold text-slate-300 uppercase tracking-wide text-[10px]">User Query</span>
                        <button onClick={() => copy(selected.query, 'q')} className="flex items-center gap-1 hover:text-cyan-400 cursor-pointer transition-colors">
                          {copied === 'q' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                      <div className="bg-slate-950/90 rounded-lg px-3.5 py-3 text-xs text-slate-300 border border-slate-800 hover:border-slate-700 transition-colors">
                        {selected.query}
                      </div>
                    </div>

                    {/* Attack payload (Vivid Red Accents) */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-rose-400 uppercase tracking-wide text-[10px]">Injected Adversarial Payload</span>
                        <button onClick={() => copy(selected.document, 'p')} className="flex items-center gap-1 text-slate-400 hover:text-rose-300 cursor-pointer transition-colors">
                          {copied === 'p' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                      <div className="bg-rose-950/25 rounded-lg px-3.5 py-3 text-xs text-rose-200 border border-rose-500/30 max-h-32 overflow-y-auto leading-relaxed hover:border-rose-500/50 transition-colors">
                        {selected.document}
                      </div>
                    </div>
                  </div>

                  {/* Execute Button with Red or Green Accents */}
                  <div className="flex items-center justify-between pt-2 font-mono">
                    <span className="text-xs text-slate-400">
                      Mode: <strong className={mode === 'hardened' ? 'text-emerald-400 font-bold uppercase' : 'text-rose-400 font-bold uppercase'}>{mode}</strong>
                    </span>
                    <button
                      onClick={runAttack}
                      disabled={loading}
                      className={`flex items-center gap-2 px-6 py-2.5 rounded text-xs font-bold font-mono tracking-wider cursor-pointer disabled:opacity-50 transition-all duration-200 hover:-translate-y-0.5 active:scale-95 text-white ${
                        mode === 'hardened'
                          ? 'bg-emerald-600 hover:bg-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.5)]'
                          : 'bg-rose-600 hover:bg-rose-500 shadow-[0_0_20px_rgba(244,63,94,0.5)]'
                      }`}
                    >
                      {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                      <span>EXECUTE ATTACK</span>
                    </button>
                  </div>
                </div>

                {/* Results with Vivid Red & Green Accents */}
                {result && (
                  <div className="space-y-4 font-mono transition-all duration-300">
                    {/* Verdict */}
                    <div className={`panel px-6 py-4 flex items-center justify-between ${
                      result.blocked 
                        ? 'border-emerald-500/50 bg-emerald-950/25 shadow-[0_0_25px_rgba(16,185,129,0.2)]' 
                        : 'border-rose-500/50 bg-rose-950/25 shadow-[0_0_25px_rgba(244,63,94,0.2)]'
                    }`}>
                      <div className="flex items-center gap-3.5">
                        {result.blocked
                          ? <ShieldCheck className="w-6 h-6 text-emerald-400 animate-bounce" />
                          : <ShieldAlert className="w-6 h-6 text-rose-400 animate-pulse" />
                        }
                        <div>
                          <div className={`text-base font-bold ${result.blocked ? 'text-emerald-300' : 'text-rose-300'}`}>
                            {result.blocked ? 'ATTACK DEFENDED' : 'ATTACK SUCCEEDED (SYSTEM COMPROMISED)'}
                          </div>
                          {result.blocked_by && (
                            <div className="text-xs text-slate-400 mt-0.5">{result.blocked_by}</div>
                          )}
                        </div>
                      </div>

                      <div className="flex gap-6 text-xs">
                        <div className="text-right">
                          <div className="text-slate-500 text-[10px] uppercase font-bold">Secret Leak</div>
                          <div className={`font-bold ${result.secret_leaked ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {result.secret_leaked ? 'YES (LEAKED)' : 'NONE'}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-slate-500 text-[10px] uppercase font-bold">Tool Status</div>
                          <div className={`font-bold ${result.tool_executed ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {result.tool_executed ? 'EXECUTED' : 'BLOCKED'}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Pipeline steps */}
                    <div className="panel p-6 space-y-4 bg-[#060c18]/85 border-cyan-900/40">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                        Pipeline Decision Trace
                      </h3>

                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                        {[
                          {
                            label: 'Input Guard',
                            value: result.injection_detected ? 'Flagged' : 'Clean',
                            ok: !result.injection_detected,
                          },
                          {
                            label: 'LLM Intent',
                            value: result.requested_tool || 'Refused',
                            ok: !result.model_compromised,
                          },
                          {
                            label: 'Tool Policy',
                            value: result.tool_authorized ? 'Allowed' : 'Denied',
                            ok: !result.tool_authorized,
                          },
                          {
                            label: 'Output Guard',
                            value: result.secret_leaked ? 'Leaked' : 'Safe',
                            ok: !result.secret_leaked,
                          },
                        ].map((step, i) => (
                          <div key={i} className="bg-slate-950 p-3.5 rounded border border-slate-800 hover:border-slate-700 transition-colors">
                            <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">{step.label}</div>
                            <div className={`font-bold ${step.ok ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {step.value}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Tool calls */}
                      {result.tool_calls?.length > 0 && (
                        <div className="space-y-2">
                          <h4 className="text-[11px] font-bold uppercase text-slate-400">Tool Calls</h4>
                          {result.tool_calls.map((tc, i) => (
                            <div key={i} className={`flex items-center justify-between px-3.5 py-2.5 rounded text-xs ${
                              tc.blocked
                                ? 'bg-rose-950/30 border border-rose-500/30 text-rose-300 shadow-[0_0_10px_rgba(244,63,94,0.15)]'
                                : 'bg-slate-950 border border-slate-800 text-slate-300'
                            }`}>
                              <span>{tc.tool}</span>
                              <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                                tc.blocked ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                              }`}>
                                {tc.blocked ? 'denied by policy' : 'executed'}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Response */}
                      <div className="space-y-2">
                        <h4 className="text-[11px] font-bold uppercase text-slate-400">Agent Response</h4>
                        <div className={`rounded-lg px-4 py-3.5 text-xs leading-relaxed border ${
                          result.secret_leaked 
                            ? 'bg-rose-950/30 border-rose-500/40 text-rose-200' 
                            : 'bg-slate-950 border border-slate-800 text-slate-300'
                        }`}>
                          {result.final_result}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="panel p-16 text-center text-slate-500 text-sm font-mono">
                Select an attack scenario from the left to view details and execute.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── QUERY TAB ── */}
      {tab === 'query' && (
        <div className="max-w-3xl space-y-5 font-mono">
          <div className="panel p-6 space-y-4 bg-[#060c18]/85 border-cyan-900/40">
            <textarea
              value={query}
              onChange={e => setQuery(e.target.value)}
              rows={2}
              placeholder="Ask a question about company policies..."
              className="w-full bg-slate-950 border border-slate-800 rounded p-3.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 resize-none transition-colors"
            />

            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-1.5">
                {['What is the leave policy?', 'How does incident response work?', 'Travel reimbursement rules?'].map((s, i) => (
                  <button
                    key={i}
                    onClick={() => { setQuery(s); runQuery(s); }}
                    className="px-2.5 py-1 rounded bg-slate-900 hover:bg-cyan-950/40 hover:text-cyan-300 hover:border-cyan-500/40 text-[11px] text-slate-400 border border-slate-800 cursor-pointer transition-all hover:scale-105"
                  >
                    {s}
                  </button>
                ))}
              </div>
              <button
                onClick={() => runQuery()}
                disabled={loading || !query.trim()}
                className="btn-cyber-primary flex items-center gap-1.5 px-5 py-2.5 rounded text-xs font-black cursor-pointer disabled:opacity-40"
              >
                {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                RUN QUERY
              </button>
            </div>
          </div>

          {queryResult && (
            <div className="space-y-4">
              <div className={`panel px-5 py-3.5 flex items-center gap-3 ${
                queryResult.security?.blocked_actions?.length
                  ? 'border-rose-500/40 bg-rose-950/20 shadow-[0_0_15px_rgba(244,63,94,0.15)]'
                  : 'border-emerald-500/40 bg-emerald-950/20 shadow-[0_0_15px_rgba(16,185,129,0.15)]'
              }`}>
                {queryResult.security?.blocked_actions?.length
                  ? <ShieldAlert className="w-5 h-5 text-rose-400" />
                  : <ShieldCheck className="w-5 h-5 text-emerald-400" />
                }
                <span className="text-xs font-bold text-slate-200">
                  {queryResult.security?.blocked_actions?.length
                    ? 'Security policy triggered'
                    : 'Query processed normally'}
                </span>
                <span className="ml-auto text-[11px] font-mono text-cyan-400 bg-slate-950 px-2.5 py-0.5 rounded border border-slate-800">
                  Risk: {queryResult.security?.input_risk?.toUpperCase() || 'LOW'}
                </span>
              </div>

              {queryResult.retrieved_documents?.length > 0 && (
                <div className="panel p-5 space-y-2.5 bg-[#060c18]/85 border-cyan-900/40">
                  <h4 className="text-[11px] font-bold uppercase text-slate-400">Retrieved Knowledge Chunks ({queryResult.retrieved_documents.length})</h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {queryResult.retrieved_documents.map((doc, i) => (
                      <div key={i} className="bg-slate-950 px-3.5 py-2.5 rounded text-[11px] text-slate-400 font-mono border border-slate-800 hover:border-slate-700 transition-colors">
                        {doc}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="panel p-6 space-y-2 bg-[#060c18]/85 border-cyan-900/40">
                <h4 className="text-[11px] font-bold uppercase text-slate-400">Response</h4>
                <div className="text-sm text-slate-200 leading-relaxed font-sans">
                  {queryResult.answer}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
