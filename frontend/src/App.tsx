import { useState } from 'react';
import AuditLog from './pages/AuditLog';
import ChatBridge from './pages/ChatBridge';
import Dashboard from './pages/Dashboard';
import Findings from './pages/Findings';
import ProjectDetails from './pages/ProjectDetails';
import Projects from './pages/Projects';
import Rules from './pages/Rules';
import Runs from './pages/Runs';
import Settings from './pages/Settings';
import Sources from './pages/Sources';
import Updates from './pages/Updates';

type PageKey =
  | 'dashboard'
  | 'projects'
  | 'project-details'
  | 'findings'
  | 'runs'
  | 'updates'
  | 'rules'
  | 'sources'
  | 'chat-bridge'
  | 'audit-log'
  | 'settings';

const navItems: { label: string; page: PageKey }[] = [
  { label: 'Dashboard', page: 'dashboard' },
  { label: 'Projects', page: 'projects' },
  { label: 'Project Details', page: 'project-details' },
  { label: 'Findings', page: 'findings' },
  { label: 'Runs', page: 'runs' },
  { label: 'Updates', page: 'updates' },
  { label: 'Rules', page: 'rules' },
  { label: 'Sources', page: 'sources' },
  { label: 'Chat Bridge', page: 'chat-bridge' },
  { label: 'Audit Log', page: 'audit-log' },
  { label: 'Settings', page: 'settings' },
];

export default function App() {
  const [page, setPage] = useState<PageKey>('dashboard');

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">CQ</span>
          <span>codex-quality-gate</span>
        </div>
        <nav>
          {navItems.map((item) => (
            <button
              className={item.page === page ? 'nav-item active' : 'nav-item'}
              key={item.page}
              onClick={() => setPage(item.page)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
      {renderPage(page)}
    </main>
  );
}

function renderPage(page: PageKey) {
  switch (page) {
    case 'projects':
      return <Projects />;
    case 'project-details':
      return <ProjectDetails />;
    case 'findings':
      return <Findings />;
    case 'runs':
      return <Runs />;
    case 'updates':
      return <Updates />;
    case 'rules':
      return <Rules />;
    case 'sources':
      return <Sources />;
    case 'chat-bridge':
      return <ChatBridge />;
    case 'audit-log':
      return <AuditLog />;
    case 'settings':
      return <Settings />;
    case 'dashboard':
    default:
      return <Dashboard />;
  }
}
