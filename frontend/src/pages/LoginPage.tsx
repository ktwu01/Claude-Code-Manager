import { useState } from 'react';
import { setToken } from '../api/client';
import { getApiBase, getServerUrl, setServerUrl } from '../config/server';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface LoginPageProps {
  onLogin: () => void;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [token, setTokenValue] = useState('');
  const [serverUrl, setServerUrlValue] = useState(getServerUrl());
  const [showServer, setShowServer] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Save server URL if changed
    if (serverUrl !== getServerUrl()) {
      setServerUrl(serverUrl);
    }

    const base = serverUrl.replace(/\/+$/, '') || getApiBase();
    try {
      const res = await fetch(`${base}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });
      if (res.ok) {
        setToken(token);
        onLogin();
      } else {
        setError('Invalid token');
      }
    } catch {
      setError('Connection failed. Check server URL.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <form onSubmit={handleSubmit} className="bg-gray-800 rounded-lg p-6 w-full max-w-sm space-y-4">
        <h1 className="text-foreground text-lg font-bold text-center">Claude Code Manager</h1>
        <p className="text-gray-400 text-sm text-center">Enter your access token</p>
        <input
          type="password"
          className="w-full bg-gray-700 text-foreground rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Token"
          value={token}
          onChange={(e) => setTokenValue(e.target.value)}
          autoFocus
          required
        />
        <div>
          <button
            type="button"
            onClick={() => setShowServer(!showServer)}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            {showServer ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            Server URL
          </button>
          {showServer && (
            <input
              type="url"
              className="w-full bg-gray-700 text-foreground rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mt-1"
              placeholder="https://your-server.com (leave empty for same origin)"
              value={serverUrl}
              onChange={(e) => setServerUrlValue(e.target.value)}
            />
          )}
        </div>
        {error && <p className="text-red-400 text-xs">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded text-sm font-medium disabled:opacity-50"
        >
          {loading ? 'Verifying...' : 'Login'}
        </button>
      </form>
    </div>
  );
}
