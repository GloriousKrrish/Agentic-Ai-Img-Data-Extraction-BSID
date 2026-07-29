import React from 'react';
import { 
  LayoutDashboard, 
  Upload, 
  Clock, 
  Table
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, pendingCount = 0 }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', label: 'Upload & Process', icon: Upload },
    { id: 'processing', label: 'Processing Queue', icon: Clock, badge: pendingCount ? `${pendingCount}` : undefined },
    { id: 'results', label: 'Results (Live Excel)', icon: Table, highlight: true },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between h-screen sticky top-0 z-30 select-none shadow-xs">
      {/* Brand Header */}
      <div>
        <div className="p-5 border-b border-slate-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#E60012] flex items-center justify-center text-white font-black text-lg shadow-xs">
            B
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-slate-900 text-sm tracking-tight">BRIDGESTONE</span>
              <span className="text-[10px] font-bold px-1.5 py-0.2 bg-red-100 text-[#E60012] rounded">AI</span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Document Intelligence</p>
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
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                  isActive
                    ? 'bg-[#E600120D] text-[#E60012] border border-[#E6001220]'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#E60012]' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                
                {item.badge && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-[#E6001215] text-[#E60012]">
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
      <div className="p-4 border-t border-slate-100 text-[11px] text-slate-400">
        Bridgestone AI Extraction Engine v2.0
      </div>
    </aside>
  );
};
