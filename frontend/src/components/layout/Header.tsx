import React from 'react';
import { Radio, RefreshCw, Zap } from 'lucide-react';

interface HeaderProps {
  wsConnected: boolean;
  onRefresh?: () => void;
  title?: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ wsConnected, onRefresh, title = "Enterprise Document Intelligence Platform", subtitle = "Real-time Agentic Extraction Engine" }) => {
  return (
    <header className="h-16 bg-white/80 backdrop-blur-md border-b border-[#ECECEC] px-8 flex items-center justify-between sticky top-0 z-20 shadow-2xs">
      <div>
        <h1 className="text-base font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
          {title}
          <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 bg-[#005BAC10] text-[#005BAC] font-bold rounded-full border border-[#005BAC25]">
            Enterprise Tier
          </span>
        </h1>
        <p className="text-xs text-[#6B7280] font-medium">{subtitle}</p>
      </div>

      <div className="flex items-center gap-4">
        {/* WebSocket Status Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F8FAFC] border border-[#E2E8F0]">
          <span className="relative flex h-2 w-2">
            {wsConnected ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            )}
          </span>
          <span className="text-xs font-semibold text-[#334155] flex items-center gap-1.5">
            <Radio className="w-3 h-3 text-[#005BAC]" />
            {wsConnected ? 'Live Socket Sync' : 'Reconnecting...'}
          </span>
        </div>

        {/* Engine Pipeline Status */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F8FAFC] border border-[#E2E8F0]">
          <Zap className="w-3.5 h-3.5 text-[#E60012]" />
          <span className="text-xs font-semibold text-[#334155]">3 Parallel Workers Active</span>
        </div>

        {/* Action Button */}
        {onRefresh && (
          <button 
            onClick={onRefresh} 
            className="p-2 text-[#64748B] hover:text-[#1E293B] hover:bg-[#F1F5F9] rounded-lg transition-colors border border-[#E2E8F0]"
            title="Refresh System Data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}

        {/* Enterprise Profile Pill */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-[#ECECEC]">
          <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center text-xs shadow-xs">
            BS
          </div>
          <div className="hidden lg:block">
            <div className="text-xs font-bold text-[#1E293B]">Bridgestone Admin</div>
            <div className="text-[10px] text-[#64748B] font-medium">India Operations</div>
          </div>
        </div>
      </div>
    </header>
  );
};
