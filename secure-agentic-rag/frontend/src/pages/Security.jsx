import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, FileCode, CheckCircle2, ChevronRight, 
  AlertTriangle 
} from 'lucide-react';
import { api } from '../services/api';

export default function Security() {
  const [layers, setLayers] = useState([]);
  const [activeLayer, setActiveLayer] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSecurityLayers()
      .then((data) => {
        setLayers(data);
        if (data.length > 0) setActiveLayer(data[0]);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-8 font-mono">
      {/* Header */}
      <div className="pb-4 border-b border-cyan-950/40">
        <div className="text-cyan-400 text-xs font-bold tracking-widest flex items-center gap-2 mb-1">
          <span>//</span>
          <span>APPLICATION-LAYER CONTROLS</span>
        </div>
        <h1 className="text-3xl font-black text-white tracking-tight uppercase">The 6 Defense-in-Depth Layers</h1>
        <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed font-sans">
          Deterministic application-layer security enforced in Python. Security cannot rely on the LLM's willingness to follow system prompts.
        </p>
      </div>

      {/* Layer Navigation Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
        {layers.map((l) => (
          <button
            key={l.id}
            onClick={() => setActiveLayer(l)}
            className={`p-3 rounded border text-left transition-all cursor-pointer ${
              activeLayer?.id === l.id
                ? 'border-cyan-400 bg-cyan-950/40 text-white shadow-[0_0_15px_rgba(6,182,212,0.3)]'
                : 'border-slate-800/80 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200'
            }`}
          >
            <div className="text-[10px] text-cyan-400 font-bold uppercase">Layer 0{l.id}</div>
            <div className="font-bold text-xs truncate mt-1 text-slate-200">{l.name}</div>
          </button>
        ))}
      </div>

      {/* Active Layer Deep Dive Card */}
      {activeLayer && (
        <div className="panel p-6 sm:p-8 space-y-6 bg-[#060c18]/85 border-cyan-900/40 shadow-[0_0_20px_rgba(6,182,212,0.1)]">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-5 border-b border-slate-800">
            <div>
              <div className="text-[11px] text-cyan-400 uppercase font-bold tracking-wider">
                Defense Layer 0{activeLayer.id}
              </div>
              <h2 className="text-2xl font-bold text-white mt-0.5">{activeLayer.name}</h2>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5 text-slate-500" />
                <span>Source File: <code className="text-cyan-300 bg-slate-900 px-1.5 py-0.5 rounded font-bold border border-slate-800">{activeLayer.file}</code></span>
              </p>
            </div>

            <div className="px-3 py-1 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center gap-1.5 self-start sm:self-auto">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>ACTIVE IN HARDENED MODE</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            {/* Left: Purpose and Action */}
            <div className="space-y-4">
              <div className="space-y-1.5">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Purpose & Mechanism
                </h3>
                <p className="text-slate-300 leading-relaxed bg-slate-950 p-4 rounded border border-slate-800 font-sans text-[12px]">
                  {activeLayer.description}
                </p>
              </div>

              <div className="space-y-1.5">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Action on Threat Detection
                </h3>
                <div className="flex items-start gap-2.5 p-3.5 rounded bg-amber-950/20 border border-amber-500/30 text-amber-300 text-xs font-mono">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-400" />
                  <span>{activeLayer.action_on_trigger}</span>
                </div>
              </div>
            </div>

            {/* Right: Threats Prevented */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Threat Classes Neutralized
              </h3>

              <div className="space-y-2">
                {activeLayer.protects_against?.map((threat, idx) => (
                  <div key={idx} className="flex items-center gap-2.5 p-3 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200">
                    <ShieldCheck className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                    <span>{threat}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Visual Pipeline Flow */}
      <div className="panel p-6 space-y-3.5 bg-[#060c18]/85 border-cyan-900/40">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
          End-to-End Pipeline Execution Map
        </h3>

        <div className="overflow-x-auto py-2">
          <div className="flex items-center gap-1.5 min-w-[720px] text-xs">
            <div className="px-3 py-1.5 rounded bg-slate-900 border border-slate-700 text-slate-300 text-[11px]">User Query</div>
            <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
            <div className="px-3 py-1.5 rounded bg-rose-950/40 border border-rose-500/40 text-rose-300 text-[11px] font-bold">1. Input Guard</div>
            <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
            <div className="px-3 py-1.5 rounded bg-slate-900 border border-slate-700 text-slate-300 text-[11px]">Retriever</div>
            <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
            <div className="px-3 py-1.5 rounded bg-orange-950/40 border border-orange-500/40 text-orange-300 text-[11px] font-bold">2. Untrusted Boundary</div>
            <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
            <div className="px-3 py-1.5 rounded bg-slate-900 border border-slate-700 text-slate-300 text-[11px]">LLM</div>
            <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
            <div className="px-3 py-1.5 rounded bg-amber-950/40 border border-amber-500/40 text-amber-300 text-[11px] font-bold">3. Structured Schema</div>
            <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
            <div className="px-3 py-1.5 rounded bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-[11px] font-bold">4. Tool Policy</div>
            <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
            <div className="px-3 py-1.5 rounded bg-sky-950/40 border border-sky-500/40 text-sky-300 text-[11px] font-bold">5. Arg Validator</div>
            <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
            <div className="px-3 py-1.5 rounded bg-purple-950/40 border border-purple-500/40 text-purple-300 text-[11px] font-bold">6. Output Guard</div>
          </div>
        </div>
      </div>
    </div>
  );
}
