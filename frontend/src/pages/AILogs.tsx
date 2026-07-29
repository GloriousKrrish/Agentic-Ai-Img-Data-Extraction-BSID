import React, { useState } from 'react';
import { Search } from 'lucide-react';
import type { LogEntry } from '../types';

interface AILogsProps {
  logs: LogEntry[];
}

export const AILogs: React.FC<AILogsProps> = ({ logs }) => {
  const [filterLevel, setFilterLevel] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filteredLogs = logs.filter(l => {
    const matchesLevel = filterLevel === "ALL" || l.level === filterLevel;
    const matchesSearch = l.message.toLowerCase().includes(searchQuery.toLowerCase()) || l.worker.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesLevel && matchesSearch;
  });

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-[#1B1B1B] tracking-tight">Real-Time AI Log Console</h2>
          <p className="text-xs text-[#6B7280]">Live terminal stream from worker processes & Gemini API requests</p>
        </div>

        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-xs font-bold text-slate-700">Live Worker Stream</span>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="glass-card rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-[#94A3B8] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input 
            type="text" 
            placeholder="Search terminal logs..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl text-xs font-semibold text-[#1E293B] focus:outline-none focus:border-[#005BAC]"
          />
        </div>

        <div className="flex items-center gap-2">
          {["ALL", "INFO", "SUCCESS", "WARN", "ERROR"].map(lvl => (
            <button
              key={lvl}
              onClick={() => setFilterLevel(lvl)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                filterLevel === lvl 
                  ? 'bg-slate-900 text-white' 
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Terminal View Box */}
      <div className="bg-slate-950 text-slate-200 rounded-2xl p-6 font-mono text-xs shadow-2xl border border-slate-800 space-y-2 max-h-[550px] overflow-y-auto">
        {filteredLogs.length > 0 ? (
          filteredLogs.map((log, idx) => (
            <div key={idx} className="flex items-start gap-3 py-1 border-b border-slate-900/60 hover:bg-slate-900/40 px-2 rounded">
              <span className="text-slate-500 text-[10px] shrink-0">{log.timestamp}</span>
              <span className="text-[#005BAC] font-bold shrink-0">[{log.worker}]</span>
              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold shrink-0 ${
                log.level === 'ERROR' ? 'bg-red-950 text-red-400 border border-red-800' :
                log.level === 'SUCCESS' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                log.level === 'WARN' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                'bg-slate-800 text-slate-300'
              }`}>
                {log.level}
              </span>
              <span className="text-slate-300 leading-relaxed break-all">{log.message}</span>
            </div>
          ))
        ) : (
          <div className="py-12 text-center text-slate-500">
            No log entries found matching filter.
          </div>
        )}
      </div>
    </div>
  );
};
