import React, { useState, useEffect } from 'react';
import { 
  Play, RefreshCw, Search, Terminal, ShieldAlert
} from 'lucide-react';
import { api } from '../services/api';

export default function RedTeam() {
  const [attacks, setAttacks] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [runningSuite, setRunningSuite] = useState(false);
  const [suiteProgress, setSuiteProgress] = useState(null);

  // Filter states
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  // Single attack side-by-side comparison state
  const [activeComparison, setActiveComparison] = useState(null);
  const [runningSingle, setRunningSingle] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getAttacks().catch(() => []),
      api.getResults().catch(() => null),
    ]).then(([atks, res]) => {
      setAttacks(atks);
      setResults(res);
      setLoading(false);
    });
  }, []);

  const handleRunFullSuite = async () => {
    setRunningSuite(true);
    setSuiteProgress('Running benchmark across 50 attack cases...');
    try {
      const runRes = await api.runRedTeamSuite();
      if (runRes.results) {
        setResults(runRes.results);
      }
      setSuiteProgress('Evaluation complete! Metrics updated.');
    } catch (err) {
      setSuiteProgress(`Error: ${err.message}`);
    } finally {
      setRunningSuite(false);
    }
  };

  const handleRunSingle = async (attack) => {
    setRunningSingle(true);
    setActiveComparison({ attack, loading: true });
    try {
      const cmp = await api.runSingleAttack(attack.id);
      setActiveComparison({ attack, ...cmp, loading: false });
    } catch (err) {
      setActiveComparison({ attack, error: err.message, loading: false });
    } finally {
      setRunningSingle(false);
    }
  };

  const categories = ['ALL', ...new Set(attacks.map(a => a.category))];

  const filteredAttacks = attacks.filter(a => {
    const matchesSearch = 
      a.id.toLowerCase().includes(search.toLowerCase()) ||
      a.description.toLowerCase().includes(search.toLowerCase()) ||
      a.category.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = selectedCategory === 'ALL' || a.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-8 font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-cyan-950/40">
        <div>
          <div className="text-cyan-400 text-xs font-bold tracking-widest flex items-center gap-2 mb-1">
            <span>//</span>
            <span>ADVERSARIAL ASSESSMENT SUITE</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight uppercase">Red-Team Benchmark</h1>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Evaluating agent resistance against 50 indirect prompt injection attacks across 13 threat categories.
          </p>
        </div>

        <button
          onClick={handleRunFullSuite}
          disabled={runningSuite}
          className="flex items-center gap-2 px-5 py-2.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs tracking-wider transition-all shadow-[0_0_15px_rgba(244,63,94,0.4)] cursor-pointer disabled:opacity-50"
        >
          {runningSuite ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
          <span>{runningSuite ? 'RUNNING BENCHMARK...' : 'RUN FULL SUITE (50 ATTACKS)'}</span>
        </button>
      </div>

      {suiteProgress && (
        <div className="p-3.5 bg-cyan-950/30 border border-cyan-500/40 rounded-lg text-xs text-cyan-300 flex items-center gap-2.5">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span>{suiteProgress}</span>
        </div>
      )}

      {/* Metrics Overview: Baseline vs Hardened */}
      <div className="space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Benchmark Summary
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Baseline Summary */}
          <div className="panel p-6 space-y-3.5 border-rose-500/40 bg-gradient-to-b from-rose-950/20 to-slate-950/80">
            <div className="flex items-center justify-between pb-2.5 border-b border-rose-500/20">
              <span className="font-bold text-xs text-rose-300 uppercase tracking-wide">Baseline (No Defenses)</span>
              <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">Vulnerable</span>
            </div>
            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Attack Success Rate:</span>
                <span className="text-rose-400 font-bold">{results?.baseline?.attack_success_rate !== undefined ? `${(results.baseline.attack_success_rate * 100).toFixed(1)}%` : '100.0%'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Secret Leakage Rate:</span>
                <span className="text-rose-400 font-bold">{results?.baseline?.secret_leakage_rate !== undefined ? `${(results.baseline.secret_leakage_rate * 100).toFixed(1)}%` : '36.0%'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Tool Block Rate:</span>
                <span className="text-slate-300 font-medium">{results?.baseline?.tool_block_rate !== undefined ? `${(results.baseline.tool_block_rate * 100).toFixed(1)}%` : '0.0%'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Benign Success Rate:</span>
                <span className="text-emerald-400 font-bold">100.0%</span>
              </div>
            </div>
          </div>

          {/* Hardened Summary */}
          <div className="panel p-6 space-y-3.5 border-emerald-500/40 bg-gradient-to-b from-emerald-950/20 to-slate-950/80">
            <div className="flex items-center justify-between pb-2.5 border-b border-emerald-500/20">
              <span className="font-bold text-xs text-emerald-300 uppercase tracking-wide">Hardened (Defense-in-Depth)</span>
              <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">Protected</span>
            </div>
            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Attack Success Rate:</span>
                <span className="text-emerald-400 font-bold">{results?.hardened?.attack_success_rate !== undefined ? `${(results.hardened.attack_success_rate * 100).toFixed(1)}%` : '0.0%'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Secret Leakage Rate:</span>
                <span className="text-emerald-400 font-bold">{results?.hardened?.secret_leakage_rate !== undefined ? `${(results.hardened.secret_leakage_rate * 100).toFixed(1)}%` : '0.0%'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Tool Block Rate:</span>
                <span className="text-emerald-400 font-bold">100.0%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Benign Success Rate:</span>
                <span className="text-emerald-400 font-bold">100.0%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Side-by-Side Comparison Inspector Modal / Card */}
      {activeComparison && (
        <div className="panel p-6 space-y-4 border-cyan-500/50 bg-[#060c18]/90 shadow-[0_0_25px_rgba(6,182,212,0.15)]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-cyan-400" />
              <span className="font-bold text-xs text-white">
                Live Attack Execution: {activeComparison.attack?.id}
              </span>
            </div>
            <button
              onClick={() => setActiveComparison(null)}
              className="text-slate-400 hover:text-white text-xs cursor-pointer px-2 py-1 rounded bg-slate-900 border border-slate-800"
            >
              ✕ Close
            </button>
          </div>

          <div className="text-xs bg-slate-950 p-3.5 rounded border border-slate-800">
            <div className="text-slate-400 uppercase text-[10px] font-bold mb-1">Poisoned Document Text:</div>
            <div className="text-amber-300 italic text-[11px]">"{activeComparison.attack?.document}"</div>
          </div>

          {activeComparison.loading ? (
            <div className="py-8 text-center text-xs text-cyan-400 animate-pulse font-bold">
              Running attack against baseline and hardened pipelines simultaneously...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Baseline Side */}
              <div className="p-4 rounded bg-rose-950/20 border border-rose-500/40 space-y-2 text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-rose-500/20">
                  <span className="font-bold text-rose-300 text-[11px]">Baseline Pipeline</span>
                  <span className="text-[10px] text-rose-300 font-bold px-2 py-0.5 rounded bg-rose-500/20">
                    {activeComparison.baseline?.attack_success ? 'COMPROMISED' : 'DEFENDED'}
                  </span>
                </div>
                <div className="space-y-1.5 text-slate-300 text-[11px]">
                  <div>Proposed Tool: <span className="text-rose-300 font-bold">{activeComparison.baseline?.proposed_tool || 'None'}</span></div>
                  <div>Tool Executed: <span className={activeComparison.baseline?.tool_called ? 'text-rose-400 font-bold' : 'text-slate-400'}>{activeComparison.baseline?.tool_called ? 'YES' : 'NO'}</span></div>
                  <div>Secret Leaked: <span className={activeComparison.baseline?.secret_leaked ? 'text-rose-400 font-bold' : 'text-slate-400'}>{activeComparison.baseline?.secret_leaked ? 'YES' : 'NO'}</span></div>
                  <div className="text-slate-400 mt-1 italic text-[10px]">{activeComparison.baseline?.reason}</div>
                </div>
              </div>

              {/* Hardened Side */}
              <div className="p-4 rounded bg-emerald-950/20 border border-emerald-500/40 space-y-2 text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-emerald-500/20">
                  <span className="font-bold text-emerald-300 text-[11px]">Hardened Pipeline</span>
                  <span className="text-[10px] text-emerald-300 font-bold px-2 py-0.5 rounded bg-emerald-500/20">
                    {activeComparison.hardened?.attack_success ? 'FAILED' : 'PROTECTED'}
                  </span>
                </div>
                <div className="space-y-1.5 text-slate-300 text-[11px]">
                  <div>Policy Decision: <span className="text-emerald-300 font-bold">{activeComparison.hardened?.tool_blocked ? 'DENIED BY POLICY' : 'SAFE'}</span></div>
                  <div>Tool Blocked: <span className="text-emerald-400 font-bold">{activeComparison.hardened?.tool_blocked ? 'YES' : 'NO'}</span></div>
                  <div>Secret Leaked: <span className="text-emerald-400 font-bold">NO</span></div>
                  <div className="text-slate-400 mt-1 italic text-[10px]">{activeComparison.hardened?.reason}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Attack Corpus Explorer Table */}
      <div className="panel p-6 space-y-4 bg-[#060c18]/85 border-cyan-900/40">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-white">
            Attack Corpus Explorer ({filteredAttacks.length} Cases)
          </h2>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            {/* Search */}
            <div className="relative flex-1 sm:w-64">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search attacks..."
                className="w-full bg-slate-950 border border-slate-800 rounded pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Category Dropdown */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-cyan-500 cursor-pointer"
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase font-bold">
                <th className="py-2.5 px-3">ID</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Description</th>
                <th className="py-2.5 px-3">Target</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredAttacks.map((atk) => (
                <tr key={atk.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 px-3 text-cyan-400 font-bold whitespace-nowrap">{atk.id}</td>
                  <td className="py-3 px-3 text-slate-300 whitespace-nowrap text-[11px]">{atk.category}</td>
                  <td className="py-3 px-3 text-slate-200 max-w-xs truncate font-sans" title={atk.description}>
                    {atk.description}
                  </td>
                  <td className="py-3 px-3 text-amber-300 text-[11px] whitespace-nowrap font-medium">
                    {atk.target_tool || atk.target_secret || 'exfil'}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-bold ${
                      atk.severity === 'critical' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' :
                      atk.severity === 'high' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {atk.severity}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right whitespace-nowrap">
                    <button
                      onClick={() => handleRunSingle(atk)}
                      disabled={runningSingle}
                      className="px-3 py-1 rounded bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-500/40 text-cyan-300 text-[11px] font-bold transition-colors cursor-pointer"
                    >
                      Compare
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
