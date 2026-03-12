'use client';
import { useEffect, useRef, useState } from 'react';

const BACKEND_URL = (process.env.NEXT_PUBLIC_BACKEND_URL ?? '').replace(/\/+$/, '');
const ALLOWED_TYPES = ['application/pdf', 'text/plain'];
const ALLOWED_EXTS = ['.pdf', '.txt'];

type Status = 'idle' | 'uploading' | 'success' | 'error';

export default function DocumentUpload() {
  const [password, setPassword] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [message, setMessage] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;

    async function checkSession() {
      if (!BACKEND_URL) {
        if (!cancelled) {
          setCheckingSession(false);
          setMessage('Missing NEXT_PUBLIC_BACKEND_URL.');
          setStatus('error');
        }
        return;
      }

      try {
        const res = await fetch(`${BACKEND_URL}/admin/session`, {
          method: 'GET',
          credentials: 'include',
        });
        const data = await res.json();
        if (!cancelled) {
          setAuthenticated(Boolean(data.authenticated));
        }
      } catch {
        if (!cancelled) {
          setMessage('Could not verify admin session.');
          setStatus('error');
        }
      } finally {
        if (!cancelled) {
          setCheckingSession(false);
        }
      }
    }

    checkSession();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    if (!selected) return;
    const ext = selected.name.slice(selected.name.lastIndexOf('.')).toLowerCase();
    if (!ALLOWED_EXTS.includes(ext) && !ALLOWED_TYPES.includes(selected.type)) {
      setMessage('Only PDF and TXT files are supported.');
      setStatus('error');
      setFile(null);
      return;
    }
    setFile(selected);
    setStatus('idle');
    setMessage('');
  }

  async function handleLogin() {
    if (!password.trim()) {
      setMessage('Please enter the admin password.');
      setStatus('error');
      return;
    }

    setStatus('uploading');
    setMessage('Signing in...');

    try {
      const res = await fetch(`${BACKEND_URL}/admin/login`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setStatus('error');
        setMessage(data.detail ?? 'Login failed.');
        return;
      }
      setAuthenticated(true);
      setPassword('');
      setStatus('success');
      setMessage('✅ Admin session started.');
    } catch {
      setStatus('error');
      setMessage('Could not sign in.');
    }
  }

  async function handleLogout() {
    try {
      await fetch(`${BACKEND_URL}/admin/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } finally {
      setAuthenticated(false);
      setFile(null);
      setPassword('');
      setStatus('idle');
      setMessage('Admin session closed.');
      if (inputRef.current) inputRef.current.value = '';
    }
  }

  async function handleUpload() {
    if (!file) { setMessage('Please select a file.'); setStatus('error'); return; }
    if (!authenticated) { setMessage('Please sign in as admin first.'); setStatus('error'); return; }

    setStatus('uploading');
    setMessage('Uploading and re-indexing… this may take a minute.');

    const bytes = await file.arrayBuffer();
    const url = `${BACKEND_URL}/upload?filename=${encodeURIComponent(file.name)}`;

    try {
      const res = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 'content-type': 'application/octet-stream' },
        body: bytes,
      });
      const data = await res.json();
      if (!res.ok) {
        setStatus('error');
        setMessage(data.detail ?? `Error ${res.status}`);
        if (res.status === 401) {
          setAuthenticated(false);
        }
      } else {
        setStatus('success');
        const msg = data.status === 'indexing'
          ? `✅ "${data.filename}" uploaded. Reindexing in background — chat will be ready in ~1 minute.`
          : `✅ "${data.filename}" uploaded and indexed successfully.`;
        setMessage(msg);
        setFile(null);
        if (inputRef.current) inputRef.current.value = '';
      }
    } catch {
      setStatus('error');
      setMessage('Network error — could not reach the backend.');
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
      <button
        onClick={() => setShowPanel(v => !v)}
        className="w-full flex items-center justify-between px-5 py-4 text-left"
      >
        <span className="font-semibold text-gray-700 text-sm">📎 Upload Document</span>
        <span className="text-gray-400 text-xs">{showPanel ? '▲ hide' : '▼ show'}</span>
      </button>

      {showPanel && (
        <div className="px-5 pb-5 space-y-3 border-t border-gray-100 pt-4">
          <p className="text-xs text-gray-500">
            Upload a PDF or TXT file to the knowledge base. Access is protected by an admin session.
            After upload the index is rebuilt automatically in the background.
          </p>

          {checkingSession ? (
            <p className="text-xs text-gray-500">Checking admin session...</p>
          ) : !authenticated ? (
            <>
              <input
                type="password"
                placeholder="Admin password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
              />

              <button
                onClick={handleLogin}
                disabled={status === 'uploading'}
                className="w-full bg-slate-800 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {status === 'uploading' ? 'Signing in...' : 'Sign In as Admin'}
              </button>
            </>
          ) : (
            <div className="flex items-center justify-between rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2 text-xs text-emerald-700">
              <span>Admin session active</span>
              <button onClick={handleLogout} className="font-semibold hover:text-emerald-900">
                Log out
              </button>
            </div>
          )}

          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt"
            onChange={handleFileChange}
            disabled={!authenticated}
            className="block w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
          />

          {file && (
            <p className="text-xs text-gray-400">Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)</p>
          )}

          <button
            onClick={handleUpload}
            disabled={status === 'uploading' || !authenticated}
            className="w-full bg-emerald-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {status === 'uploading' ? 'Uploading…' : 'Upload & Re-index'}
          </button>

          {message && (
            <p className={`text-xs font-medium ${status === 'error' ? 'text-red-600' : status === 'success' ? 'text-emerald-600' : 'text-gray-500'}`}>
              {message}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
