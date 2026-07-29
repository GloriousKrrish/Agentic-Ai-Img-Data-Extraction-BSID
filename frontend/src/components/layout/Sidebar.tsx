import React from 'react';
import { 
  LayoutDashboard, 
  FileCheck, 
  Layers, 
  Cpu, 
  Table, 
  ListFilter, 
  Terminal, 
  BarChart3, 
  Settings, 
  Sparkles,
  HelpCircle
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, pendingCount = 0 }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'invoice-processing', label: 'Invoice Processing', icon: FileCheck },
    { id: 'batch-processing', label: 'Batch Engine', icon: Layers, badge: 'Flagship' },
    { id: 'live-queue', label: 'Live Queue & Nodes', icon: Cpu, badge: pendingCount ? `${pendingCount}` : undefined },
    { id: 'excel-sync', label: 'Live Excel Sync', icon: Table, highlight: true },
    { id: 'results', label: 'Results & Inspection', icon: ListFilter },
    { id: 'ai-logs', label: 'Real-Time AI Logs', icon: Terminal },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings & Models', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-[#ECECEC] flex flex-col justify-between h-screen sticky top-0 z-30 select-none shadow-xs">
      {/* Brand Header */}
      <div>
        <div className="p-5 border-b border-[#ECECEC] flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#E60012] flex items-center justify-center text-white font-bold tracking-tighter shadow-sm text-lg">
            B
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-[#1B1B1B] text-base tracking-tight">BRIDGESTONE</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 bg-[#E6001215] text-[#E60012] rounded">AI</span>
            </div>
            <p className="text-[11px] text-[#6B7280] font-medium tracking-tight">Document Intelligence</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-200 group ${
                  isActive
                    ? 'bg-[#E600120C] text-[#E60012] shadow-2xs'
                    : 'text-[#4B5563] hover:bg-[#F4F4F5] hover:text-[#1B1B1B]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-[#E60012]' : 'text-[#6B7280] group-hover:text-[#1B1B1B]'
                  }`} />
                  <span>{item.label}</span>
                </div>
                
                {item.badge && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wide ${
                    item.badge === 'Flagship'
                      ? 'bg-[#005BAC15] text-[#005BAC]'
                      : 'bg-[#E6001215] text-[#E60012]'
                  }`}>
                    {item.badge}
                  </span>
                )}
                {item.highlight && !item.badge && (
                  <span className="w-2 h-2 rounded-full bg-[#E60012] animate-pulse"></span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-[#ECECEC]">
        <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3 mb-2">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-3.5 h-3.5 text-[#005BAC]" />
            <span className="text-[11px] font-bold text-[#1E293B]">Gemini 3.5 Flash Active</span>
          </div>
          <p className="text-[10px] text-[#64748B] leading-snug">Auto-fallback enabled to 2.5 Flash node.</p>
        </div>

        <div className="flex items-center justify-between text-[11px] text-[#94A3B8] px-2 py-1">
          <span>v2.4 Enterprise</span>
          <span className="flex items-center gap-1 hover:text-[#64748B] cursor-pointer">
            <HelpCircle className="w-3 h-3" /> Docs
          </span>
        </div>
      </div>
    </aside>
  );
};
