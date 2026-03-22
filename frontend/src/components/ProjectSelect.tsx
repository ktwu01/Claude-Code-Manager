import { useState, useRef, useEffect } from 'react';
import type { Project } from '../api/client';
import { ChevronDown } from 'lucide-react';

// Stable color palette for tags — same tag always gets the same color
const TAG_COLORS = [
  'bg-blue-500/20 text-blue-300',
  'bg-emerald-500/20 text-emerald-300',
  'bg-purple-500/20 text-purple-300',
  'bg-orange-500/20 text-orange-300',
  'bg-pink-500/20 text-pink-300',
  'bg-cyan-500/20 text-cyan-300',
  'bg-yellow-500/20 text-yellow-300',
  'bg-rose-500/20 text-rose-300',
  'bg-teal-500/20 text-teal-300',
  'bg-indigo-500/20 text-indigo-300',
];

function tagColor(tag: string): string {
  let hash = 0;
  for (let i = 0; i < tag.length; i++) hash = ((hash << 5) - hash + tag.charCodeAt(i)) | 0;
  return TAG_COLORS[Math.abs(hash) % TAG_COLORS.length];
}

function TagBadge({ tag }: { tag: string }) {
  return (
    <span className={`inline-block px-1.5 py-0 rounded text-[10px] font-medium leading-4 ${tagColor(tag)}`}>
      {tag}
    </span>
  );
}

interface ProjectSelectProps {
  projects: Project[];
  value: number | string | undefined;
  onChange: (value: string) => void;
  placeholder?: string;
  extraOptions?: { value: string; label: string }[];
  className?: string;
  showStatus?: boolean;
}

export function ProjectSelect({
  projects,
  value,
  onChange,
  placeholder = 'All Projects',
  extraOptions,
  className = '',
  showStatus = false,
}: ProjectSelectProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const selected = projects.find((p) => String(p.id) === String(value));
  const displayValue = selected ? selected.name : placeholder;

  return (
    <div ref={ref} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 w-full px-2 py-1 rounded text-xs font-medium bg-gray-800 text-gray-400 hover:bg-gray-700 transition-colors text-left"
      >
        <span className="flex-1 flex items-center gap-1.5 min-w-0 truncate">
          <span className="truncate">{displayValue}</span>
          {selected && selected.tags.length > 0 && (
            <span className="flex gap-1 shrink-0">
              {selected.tags.map((t) => <TagBadge key={t} tag={t} />)}
            </span>
          )}
          {showStatus && selected && selected.status !== 'ready' && (
            <span className="text-yellow-400 text-[10px]">({selected.status})</span>
          )}
        </span>
        <ChevronDown size={12} className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-full min-w-[220px] max-h-60 overflow-auto bg-gray-800 border border-gray-700 rounded-lg shadow-xl">
          {/* Empty / placeholder option */}
          <div
            onClick={() => { onChange(''); setOpen(false); }}
            className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-gray-700 transition-colors ${
              !value ? 'text-white bg-gray-700/50' : 'text-gray-400'
            }`}
          >
            {placeholder}
          </div>

          {projects.map((p) => (
            <div
              key={p.id}
              onClick={() => { onChange(String(p.id)); setOpen(false); }}
              className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-gray-700 transition-colors flex items-center gap-1.5 ${
                String(p.id) === String(value) ? 'text-white bg-gray-700/50' : 'text-gray-300'
              }`}
            >
              <span className="truncate">{p.name}</span>
              {p.tags.length > 0 && (
                <span className="flex gap-1 shrink-0 ml-auto">
                  {p.tags.map((t) => <TagBadge key={t} tag={t} />)}
                </span>
              )}
              {showStatus && p.status !== 'ready' && (
                <span className="text-yellow-400 text-[10px] shrink-0">({p.status})</span>
              )}
            </div>
          ))}

          {extraOptions?.map((opt) => (
            <div
              key={opt.value}
              onClick={() => { onChange(opt.value); setOpen(false); }}
              className={`px-3 py-1.5 text-xs cursor-pointer hover:bg-gray-700 transition-colors border-t border-gray-700 ${
                String(value) === opt.value ? 'text-white bg-gray-700/50' : 'text-indigo-400'
              }`}
            >
              {opt.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
