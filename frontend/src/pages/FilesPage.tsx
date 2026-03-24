import { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, Folder, FolderOpen, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import type { Project } from '../api/client';

interface DirEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number | null;
}

interface TreeNodeProps {
  entry: DirEntry;
  selectedPath: string | null;
  onSelect: (path: string, isDir: boolean) => void;
}

function TreeNode({ entry, selectedPath, onSelect }: TreeNodeProps) {
  const [open, setOpen] = useState(false);
  const [children, setChildren] = useState<DirEntry[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    if (!entry.is_dir) {
      onSelect(entry.path, false);
      return;
    }
    if (!open && children === null) {
      setLoading(true);
      setError(null);
      try {
        const res = await api.listDir(entry.path);
        setChildren(res.entries);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    }
    setOpen((v) => !v);
    onSelect(entry.path, true);
  };

  const isSelected = selectedPath === entry.path;

  return (
    <div>
      <div
        onClick={handleClick}
        className={`flex items-center gap-1 px-2 py-0.5 rounded cursor-pointer text-sm select-none hover:bg-gray-700 ${
          isSelected ? 'bg-gray-700 text-indigo-400' : 'text-gray-300'
        }`}
      >
        <span className="w-4 flex-shrink-0 text-gray-500">
          {entry.is_dir ? (
            loading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : open ? (
              <ChevronDown size={14} />
            ) : (
              <ChevronRight size={14} />
            )
          ) : null}
        </span>
        {entry.is_dir ? (
          open ? <FolderOpen size={14} className="text-yellow-400 flex-shrink-0" /> : <Folder size={14} className="text-yellow-400 flex-shrink-0" />
        ) : (
          <FileText size={14} className="text-gray-400 flex-shrink-0" />
        )}
        <span className="truncate">{entry.name}</span>
        {entry.size !== null && (
          <span className="ml-auto text-xs text-gray-600 flex-shrink-0">{formatSize(entry.size)}</span>
        )}
      </div>
      {error && (
        <div className="ml-8 text-xs text-red-400 py-0.5">{error}</div>
      )}
      {open && children && (
        <div className="ml-4 border-l border-gray-700">
          {children.length === 0 && (
            <div className="ml-4 text-xs text-gray-600 py-0.5">empty</div>
          )}
          {children.map((child) => (
            <TreeNode key={child.path} entry={child} selectedPath={selectedPath} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  );
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}K`;
  return `${(bytes / 1024 / 1024).toFixed(1)}M`;
}

export function FilesPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [rootPath, setRootPath] = useState('');
  const [inputPath, setInputPath] = useState('');
  const [rootEntries, setRootEntries] = useState<DirEntry[] | null>(null);
  const [rootError, setRootError] = useState<string | null>(null);
  const [rootLoading, setRootLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  useEffect(() => {
    api.listProjects().then(setProjects).catch(() => {});
  }, []);

  const loadRoot = async (path: string) => {
    if (!path.trim()) return;
    setRootLoading(true);
    setRootError(null);
    setRootEntries(null);
    setSelectedFile(null);
    setFileContent(null);
    try {
      const res = await api.listDir(path.trim());
      setRootPath(res.path);
      setRootEntries(res.entries);
    } catch (e) {
      setRootError((e as Error).message);
    } finally {
      setRootLoading(false);
    }
  };

  const handleSelect = async (path: string, isDir: boolean) => {
    if (isDir) return;
    setSelectedFile(path);
    setFileContent(null);
    setFileError(null);
    setFileLoading(true);
    try {
      const res = await api.readFile(path);
      setFileContent(res.content);
    } catch (e) {
      setFileError((e as Error).message);
    } finally {
      setFileLoading(false);
    }
  };

  const handleProjectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const proj = projects.find((p) => String(p.id) === e.target.value);
    if (proj?.local_path) {
      setInputPath(proj.local_path);
      loadRoot(proj.local_path);
    }
  };

  return (
    <div className="space-y-4">
      {/* Path selector */}
      <div className="bg-gray-800 rounded-lg p-4 space-y-3">
        <h2 className="text-sm font-semibold text-foreground">File Browser</h2>
        <div className="flex gap-2 flex-wrap">
          {projects.filter((p) => p.local_path).length > 0 && (
            <select
              onChange={handleProjectChange}
              defaultValue=""
              className="bg-gray-700 text-gray-300 text-sm rounded px-2 py-1.5 border border-gray-600 focus:outline-none focus:border-indigo-500"
            >
              <option value="" disabled>Select project...</option>
              {projects.filter((p) => p.local_path).map((p) => (
                <option key={p.id} value={String(p.id)}>{p.name}</option>
              ))}
            </select>
          )}
          <input
            type="text"
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadRoot(inputPath)}
            placeholder="/path/to/directory"
            className="flex-1 bg-gray-700 text-gray-300 text-sm rounded px-3 py-1.5 border border-gray-600 focus:outline-none focus:border-indigo-500 min-w-48"
          />
          <button
            onClick={() => loadRoot(inputPath)}
            disabled={rootLoading || !inputPath.trim()}
            className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Browse
          </button>
        </div>
        {rootError && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <AlertCircle size={14} /> {rootError}
          </div>
        )}
      </div>

      {/* Main area */}
      {rootEntries !== null && (
        <div className="flex gap-4 h-[calc(100vh-220px)] min-h-80">
          {/* File tree */}
          <div className="w-64 flex-shrink-0 bg-gray-800 rounded-lg overflow-y-auto p-2">
            <div className="text-xs text-gray-500 px-2 pb-1 truncate" title={rootPath}>{rootPath}</div>
            {rootLoading && (
              <div className="flex items-center gap-2 px-2 py-4 text-gray-400 text-sm">
                <Loader2 size={14} className="animate-spin" /> Loading...
              </div>
            )}
            {rootEntries.length === 0 && !rootLoading && (
              <div className="text-xs text-gray-600 px-2 py-2">empty directory</div>
            )}
            {rootEntries.map((entry) => (
              <TreeNode key={entry.path} entry={entry} selectedPath={selectedFile} onSelect={handleSelect} />
            ))}
          </div>

          {/* File viewer */}
          <div className="flex-1 bg-gray-800 rounded-lg overflow-hidden flex flex-col">
            {!selectedFile && (
              <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
                Select a file to preview
              </div>
            )}
            {selectedFile && (
              <>
                <div className="px-4 py-2 border-b border-gray-700 text-xs text-gray-400 truncate" title={selectedFile}>
                  {selectedFile}
                </div>
                <div className="flex-1 overflow-auto">
                  {fileLoading && (
                    <div className="flex items-center gap-2 p-4 text-gray-400 text-sm">
                      <Loader2 size={14} className="animate-spin" /> Loading...
                    </div>
                  )}
                  {fileError && (
                    <div className="flex items-center gap-2 p-4 text-red-400 text-sm">
                      <AlertCircle size={14} /> {fileError}
                    </div>
                  )}
                  {fileContent !== null && (
                    <pre className="p-4 text-xs text-gray-300 font-mono whitespace-pre-wrap break-all leading-relaxed">
                      {fileContent}
                    </pre>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
