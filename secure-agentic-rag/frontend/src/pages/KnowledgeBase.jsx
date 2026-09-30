import React, { useState, useEffect } from 'react';
import { 
  FolderLock, Upload, Trash2, FileText, CheckCircle2, 
  AlertCircle, ShieldCheck, ShieldAlert, Database, Search, 
  Layers, Lock, Sparkles 
} from 'lucide-react';
import { api, getStoredUser } from '../services/api';
import AuthModal from '../components/AuthModal';

export default function KnowledgeBase({ currentUser, setCurrentUser }) {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  // Chat / Query state
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('hardened');
  const [querying, setQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [queryError, setQueryError] = useState(null);

  // Load user workspaces
  useEffect(() => {
    if (currentUser) {
      loadWorkspaces();
    }
  }, [currentUser]);

  // Load documents when active workspace changes
  useEffect(() => {
    if (activeWorkspace) {
      loadDocuments(activeWorkspace.id);
    }
  }, [activeWorkspace]);

  const loadWorkspaces = async () => {
    try {
      const data = await api.getWorkspaces();
      setWorkspaces(data);
      if (data.length > 0) {
        setActiveWorkspace(data[0]);
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
    }
  };

  const loadDocuments = async (wsId) => {
    setLoadingDocs(true);
    try {
      const docs = await api.getDocuments(wsId);
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const doc = await api.uploadDocument(file, activeWorkspace?.id);
      setUploadSuccess(`Successfully uploaded and indexed "${doc.original_filename}" (${doc.chunk_count} chunks)`);
      if (activeWorkspace) {
        await loadDocuments(activeWorkspace.id);
      }
      e.target.value = '';
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}" from this workspace?`)) {
      return;
    }

    try {
      await api.deleteDocument(docId);
      if (activeWorkspace) {
        await loadDocuments(activeWorkspace.id);
      }
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setQuerying(true);
    setQueryError(null);
    setQueryResult(null);

    try {
      const res = await api.queryUserRAG({
        query,
        workspace_id: activeWorkspace?.id,
        mode,
      });
      setQueryResult(res);
    } catch (err) {
      setQueryError(err.message || 'Query failed');
    } finally {
      setQuerying(false);
    }
  };

  if (!currentUser) {
    return (
      <div className="py-16 max-w-2xl mx-auto text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-cyan-950/80 border border-cyan-400 mx-auto flex items-center justify-center text-cyan-400 shadow-[0_0_30px_rgba(6,182,212,0.3)]">
          <FolderLock className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-black text-white font-mono tracking-wide uppercase">
          Private Knowledge Base
        </h1>
        <p className="text-slate-400 text-sm font-mono max-w-lg mx-auto">
          Multi-user tenant isolation is active. Please authenticate to access your private documents, isolated FAISS vector space, and defense-in-depth RAG agent.
        </p>
        <button
          onClick={() => setAuthModalOpen(true)}
          className="inline-flex items-center gap-2 py-3 px-6 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold font-mono text-xs uppercase tracking-wider transition-all shadow-[0_0_25px_rgba(6,182,212,0.5)] cursor-pointer"
        >
          <Lock className="w-4 h-4" />
          <span>Sign In / Register</span>
        </button>

        <AuthModal
          isOpen={authModalOpen}
          onClose={() => setAuthModalOpen(false)}
          onAuthSuccess={(user) => setCurrentUser(user)}
        />
      </div>
    );
  }

  const totalChunks = documents.reduce((sum, d) => sum + (d.chunk_count || 0), 0);

  return (
    <div className="py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <div className="text-cyan-400 font-mono text-xs font-bold tracking-widest flex items-center gap-2 mb-1">
            <Database className="w-4 h-4 text-cyan-400" />
            <span>// TENANT-SCOPED KNOWLEDGE BASE</span>
          </div>
          <h1 className="text-3xl font-black text-white font-mono tracking-tight uppercase">
            My Knowledge Base
          </h1>
          <p className="text-slate-400 text-xs font-mono mt-1">
            Authenticated as <span className="text-cyan-300 font-semibold">{currentUser.username}</span> • Isolated FAISS vector space
          </p>
        </div>

        {/* Workspace Info & Switcher */}
        <div className="flex items-center gap-3">
          <div className="bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-2 text-xs font-mono">
            <div className="text-slate-400 text-[10px] uppercase tracking-wider">Active Workspace</div>
            <div className="text-cyan-300 font-bold flex items-center gap-1.5 mt-0.5">
              <FolderLock className="w-3.5 h-3.5" />
              <span>{activeWorkspace?.name || 'Loading...'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-mono">TOTAL DOCUMENTS</div>
          <div className="text-2xl font-black font-mono text-white mt-1">{documents.length}</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-mono">INDEXED CHUNKS</div>
          <div className="text-2xl font-black font-mono text-cyan-400 mt-1">{totalChunks}</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-mono">RETRIEVAL ISOLATION</div>
          <div className="text-xs font-mono text-emerald-400 font-bold mt-2 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" />
            <span>Enforced (Pre-Retrieval)</span>
          </div>
        </div>
      </div>

      {/* Section 1: Upload Document */}
      <div className="bg-[#070d1d] border border-cyan-950/60 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold font-mono text-white flex items-center gap-2 uppercase tracking-wide">
            <Upload className="w-4 h-4 text-cyan-400" />
            <span>Upload Document to Knowledge Base</span>
          </h2>
          <span className="text-[11px] font-mono text-slate-400">Supported: .txt, .md, .json, .pdf</span>
        </div>

        {uploadError && (
          <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>{uploadError}</span>
          </div>
        )}

        {uploadSuccess && (
          <div className="p-3 rounded-lg bg-emerald-950/50 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-400" />
            <span>{uploadSuccess}</span>
          </div>
        )}

        <div className="flex items-center gap-4">
          <label className={`cursor-pointer inline-flex items-center gap-2 py-2.5 px-5 rounded-lg border border-dashed border-cyan-500/50 hover:border-cyan-400 bg-cyan-950/20 text-cyan-300 hover:text-white font-mono text-xs font-semibold transition-all ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
            <Upload className="w-4 h-4" />
            <span>{uploading ? 'Parsing & Indexing...' : '+ Select Document to Index'}</span>
            <input
              type="file"
              accept=".txt,.md,.json,.pdf,.csv"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Section 2: Document List */}
      <div className="bg-[#070d1d] border border-cyan-950/60 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-base font-bold font-mono text-white flex items-center gap-2 uppercase tracking-wide">
            <FileText className="w-4 h-4 text-cyan-400" />
            <span>Indexed Documents</span>
          </h2>
          <span className="text-xs font-mono text-slate-400">{documents.length} files</span>
        </div>

        {loadingDocs ? (
          <div className="text-center py-8 text-xs font-mono text-slate-400">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="text-center py-10 border border-slate-800/80 rounded-xl bg-slate-900/30">
            <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <div className="text-xs font-mono text-slate-400">Your knowledge base is empty.</div>
            <div className="text-[11px] font-mono text-slate-500 mt-1">Upload a document above to begin workspace-scoped RAG.</div>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/70">
            {documents.map((doc) => (
              <div key={doc.id} className="py-3.5 flex items-center justify-between gap-4 group">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-cyan-950/50 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-mono font-bold text-white group-hover:text-cyan-300 transition-colors">
                      {doc.original_filename}
                    </div>
                    <div className="text-[11px] font-mono text-slate-400 flex items-center gap-3 mt-0.5">
                      <span className="inline-flex items-center gap-1 text-emerald-400">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>{doc.status}</span>
                      </span>
                      <span>•</span>
                      <span>{doc.chunk_count} chunks</span>
                      <span>•</span>
                      <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteDocument(doc.id, doc.original_filename)}
                  className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors cursor-pointer"
                  title="Delete document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 3: Workspace Chat / Query */}
      <div className="bg-[#070d1d] border border-cyan-950/60 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-base font-bold font-mono text-white flex items-center gap-2 uppercase tracking-wide">
              <Search className="w-4 h-4 text-cyan-400" />
              <span>Query Workspace Knowledge</span>
            </h2>
            <p className="text-slate-400 text-xs font-mono mt-0.5">
              Questions retrieve ONLY chunks indexed in this workspace through the 6-layer defense pipeline.
            </p>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setMode('hardened')}
              className={`px-3 py-1 rounded transition-all cursor-pointer ${
                mode === 'hardened'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Hardened (6 Layers)
            </button>
            <button
              onClick={() => setMode('baseline')}
              className={`px-3 py-1 rounded transition-all cursor-pointer ${
                mode === 'baseline'
                  ? 'bg-rose-500 text-slate-950 font-bold shadow-[0_0_10px_rgba(244,63,94,0.4)]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Baseline (Vulnerable)
            </button>
          </div>
        </div>

        <form onSubmit={handleQuery} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about your uploaded documents..."
            className="flex-1 bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 font-mono"
          />
          <button
            type="submit"
            disabled={querying || !query.trim()}
            className="py-3 px-6 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold font-mono text-xs uppercase tracking-wider transition-all shadow-[0_0_20px_rgba(6,182,212,0.4)] disabled:opacity-50 flex items-center gap-2 cursor-pointer"
          >
            {querying ? (
              <span className="inline-block animate-spin rounded-full h-4 w-4 border-2 border-slate-950 border-t-transparent" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span>Ask</span>
          </button>
        </form>

        {queryError && (
          <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>{queryError}</span>
          </div>
        )}

        {queryResult && (
          <div className="space-y-4 pt-4 border-t border-slate-800 animate-in fade-in duration-200">
            {/* Answer Box */}
            <div className="bg-slate-900/80 border border-slate-700/80 rounded-xl p-5 space-y-2">
              <div className="text-[11px] font-mono text-cyan-400 uppercase tracking-widest font-bold flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Agent Response ({mode})</span>
              </div>
              <div className="text-sm font-mono text-slate-100 whitespace-pre-wrap leading-relaxed">
                {queryResult.answer}
              </div>
            </div>

            {/* Security Telemetry */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-xs font-mono">
                <div className="text-slate-400 text-[10px]">INPUT RISK</div>
                <div className={`font-bold mt-1 uppercase ${
                  queryResult.security.input_risk === 'high' ? 'text-rose-400' : 'text-emerald-400'
                }`}>
                  {queryResult.security.input_risk}
                </div>
              </div>

              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-xs font-mono">
                <div className="text-slate-400 text-[10px]">INJECTION SCAN</div>
                <div className={`font-bold mt-1 ${
                  queryResult.security.injection_detected ? 'text-rose-400' : 'text-emerald-400'
                }`}>
                  {queryResult.security.injection_detected ? 'FLAGGED' : 'PASSED'}
                </div>
              </div>

              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-xs font-mono">
                <div className="text-slate-400 text-[10px]">WORKSPACE RETRIEVAL</div>
                <div className="font-bold text-cyan-400 mt-1">
                  {queryResult.retrieved_documents?.length || 0} CHUNKS
                </div>
              </div>

              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-xs font-mono">
                <div className="text-slate-400 text-[10px]">OUTPUT FILTER</div>
                <div className={`font-bold mt-1 ${
                  queryResult.security.output_safe ? 'text-emerald-400' : 'text-rose-400'
                }`}>
                  {queryResult.security.output_safe ? 'SAFE' : 'VIOLATION'}
                </div>
              </div>
            </div>

            {/* Retrieved Chunks Drawer */}
            {queryResult.retrieved_documents && queryResult.retrieved_documents.length > 0 && (
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="text-xs font-mono font-bold text-slate-300 flex items-center gap-2">
                  <Layers className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Scoped Retrieved Chunks (Workspace Isolated)</span>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                  {queryResult.retrieved_documents.map((chunkText, idx) => (
                    <div key={idx} className="p-2.5 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300 leading-snug">
                      <span className="text-cyan-400 font-bold mr-2">[{idx + 1}]</span>
                      {chunkText}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
