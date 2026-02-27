interface HeaderProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export function Header({ currentPage, onNavigate }: HeaderProps) {
  const pages = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'tasks', label: 'Tasks' },
  ];

  return (
    <header className="bg-gray-900 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
      <h1 className="text-lg font-bold text-white">Claude Code Manager</h1>
      <nav className="flex gap-2">
        {pages.map((p) => (
          <button
            key={p.key}
            onClick={() => onNavigate(p.key)}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
              currentPage === p.key
                ? 'bg-indigo-600 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
          >
            {p.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
