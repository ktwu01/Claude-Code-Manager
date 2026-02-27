import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import type { Project } from '../../api/client';
import { Plus } from 'lucide-react';
import { VoiceButton } from '../Voice/VoiceButton';

interface TaskFormProps {
  onCreated: () => void;
}

export function TaskForm({ onCreated }: TaskFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [projectId, setProjectId] = useState<number | ''>('');
  const [targetRepo, setTargetRepo] = useState('');
  const [priority, setPriority] = useState(0);
  const [mode, setMode] = useState('auto');
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    api.listProjects().then(setProjects).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !description) return;
    if (!projectId && !targetRepo) return;
    setLoading(true);
    try {
      await api.createTask({
        title,
        description,
        project_id: projectId || undefined,
        target_repo: targetRepo || undefined,
        priority,
        mode,
      });
      setTitle('');
      setDescription('');
      setPriority(0);
      onCreated();
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-gray-800 rounded-lg p-4 space-y-3">
      <h3 className="text-sm font-semibold text-gray-300">New Task</h3>
      <div className="flex gap-2">
        <input
          className="flex-1 bg-gray-700 text-white rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <VoiceButton onTranscribed={(text) => setTitle((prev) => prev ? prev + ' ' + text : text)} />
      </div>
      <div className="flex gap-2">
        <textarea
          className="flex-1 bg-gray-700 text-white rounded px-3 py-2 text-sm h-24 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Prompt / Description (this will be sent to Claude Code)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />
        <VoiceButton onTranscribed={(text) => setDescription((prev) => prev ? prev + ' ' + text : text)} />
      </div>
      <div className="flex gap-2">
        <select
          className="flex-1 bg-gray-700 text-white rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          value={projectId}
          onChange={(e) => {
            const val = e.target.value;
            setProjectId(val ? Number(val) : '');
            if (val) setTargetRepo('');
          }}
        >
          <option value="">Select project...</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} {p.status !== 'ready' ? `(${p.status})` : ''}
            </option>
          ))}
        </select>
        <span className="text-gray-500 text-sm self-center">or</span>
        <input
          className="flex-1 bg-gray-700 text-white rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Repo path (e.g. /Users/you/project)"
          value={targetRepo}
          onChange={(e) => {
            setTargetRepo(e.target.value);
            if (e.target.value) setProjectId('');
          }}
          disabled={!!projectId}
        />
      </div>
      <div className="flex items-center gap-3 flex-wrap">
        <label className="text-sm text-gray-400">Priority:</label>
        <input
          type="number"
          className="w-20 bg-gray-700 text-white rounded px-2 py-1 text-sm"
          value={priority}
          onChange={(e) => setPriority(Number(e.target.value))}
        />
        <label className="text-sm text-gray-400 ml-2">Mode:</label>
        <select
          className="bg-gray-700 text-white rounded px-2 py-1 text-sm"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
        >
          <option value="auto">Auto (direct execute)</option>
          <option value="plan">Plan (review first)</option>
        </select>
        <button
          type="submit"
          disabled={loading}
          className="ml-auto flex items-center gap-1 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
        >
          <Plus size={16} />
          {loading ? 'Creating...' : 'Create Task'}
        </button>
      </div>
    </form>
  );
}
