import React from 'react';
import type { WorkerNode, LogEntry } from '../types';
import { Cpu, Terminal, Clock, Activity } from 'lucide-react';

interface ProcessingProps {
  workers: WorkerNode[];
  pendingTasks: number;
  activeLocks: number;
  logs: LogEntry[];
}

export const Processing: React.FC<ProcessingProps> = ({ workers, pendingTasks, activeLocks, logs }) => {

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Processing Queue & Node Telemetry</h2>
          <p className="text-xs text-slate-500 mt-1">Real-time inspection of queue locks and worker execution logs</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 bg-slate-100 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-[#005BAC]" />
            {pendingTasks} Tasks Pending
          </div>
          <div className={`px-3 py-1.5 border rounded-xl text-xs font-bold flex items-center gap-1.5 ${
            activeLocks > 0 ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-700 border-slate-200'
          }`}>
            <Activity className="w-4 h-4 text-emerald-600" />
            {activeLocks} Active Locks
          </div>
        </div>
      </div>

      {/* Real Worker Nodes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {workers.map((w) => (
          <div key={w.id} className="bg-white border border-slate-200 rounded-2xl p-6 space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-[#005BAC]" />
                <h3 className="font-bold text-slate-900 text-sm">{w.name}</h3>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                w.status === 'RUNNING' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
              }`}>
                {w.status}
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Claimed Task:</span>
                <span className="font-bold text-slate-900">{w.currentTask}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Current Stage:</span>
                <span className="font-semibold text-[#005BAC]">{w.stage}</span>
              </div>
            </div>

            <div className="p-2.5 bg-slate-900 text-slate-200 rounded-xl text-[10px] font-mono truncate">
              {w.lastLog || "Awaiting task assignment..."}
            </div>
          </div>
        ))}
      </div>

      {/* Real Worker Logs Terminal */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-slate-700" />
            <h3 className="font-bold text-slate-900 text-sm">Real Worker Execution Logs</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">worker_*.log stream</span>
        </div>

        <div className="bg-slate-950 text-slate-200 rounded-xl p-5 font-mono text-xs max-h-72 overflow-y-auto space-y-1.5">
          {logs.length > 0 ? (
            logs.map((l, i) => (
              <div key={i} className="flex items-start gap-3 border-b border-slate-900 pb-1">
                <span className="text-[#005BAC] font-bold shrink-0">[{l.worker}]</span>
                <span className="text-slate-300 leading-snug">{l.message}</span>
              </div>
            ))
          ) : (
            <div className="py-8 text-center text-slate-500 font-mono">
              Waiting for backend worker log entries...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
