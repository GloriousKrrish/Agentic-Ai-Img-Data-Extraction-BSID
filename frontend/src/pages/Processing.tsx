import React from 'react';
import type { WorkerNode, LogEntry } from '../types';
import { Terminal, Clock, Activity, Loader2, CheckCircle2, ArrowRight, FileText, Sparkles, AlertCircle } from 'lucide-react';

interface ProcessingProps {
  workers?: WorkerNode[];
  pendingTasks: number;
  activeLocks?: number;
  logs: LogEntry[];
  activeJob?: any | null;
  onNavigate?: (tab: string) => void;
}

export const Processing: React.FC<ProcessingProps> = ({ 
  pendingTasks, 
  logs,
  activeJob,
  onNavigate
}) => {
  const isCompleted = activeJob?.status === 'Completed';
  const isFailed = activeJob?.status === 'Failed';
  const isProcessing = activeJob && !isCompleted && !isFailed;
  const progress = activeJob?.progress || (isCompleted ? 100 : 0);

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Live Job Telemetry & Worker Execution</h2>
          <p className="text-xs text-slate-500 mt-1">Real-time inspection of active job pipeline, progress, and logs</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 bg-slate-100 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-[#005BAC]" />
            {pendingTasks} Tasks Pending
          </div>
          <div className={`px-3 py-1.5 border rounded-xl text-xs font-bold flex items-center gap-1.5 ${
            isProcessing ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-700 border-slate-200'
          }`}>
            <Activity className="w-4 h-4 text-emerald-600" />
            {isProcessing ? '1 Active Pipeline' : 'Idle'}
          </div>
        </div>
      </div>

      {/* Active Job Telemetry Card */}
      {activeJob ? (
        <div className="glass-card bg-white border border-slate-200 rounded-2xl p-6 shadow-md space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-[#E6001210] text-[#E60012] rounded-xl">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-extrabold text-slate-900 text-base">{activeJob.filename || "Uploaded File"}</h3>
                  <span className="text-xs text-slate-400 font-mono">({activeJob.job_id})</span>
                </div>
                <p className="text-xs text-slate-500 font-medium">Category: {activeJob.document_category || "Universal Document"}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 ${
                isCompleted ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' :
                isFailed ? 'bg-red-100 text-red-800 border border-red-300' :
                'bg-blue-100 text-blue-800 border border-blue-300 animate-pulse'
              }`}>
                {isProcessing && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                {isCompleted && <CheckCircle2 className="w-3.5 h-3.5" />}
                {isFailed && <AlertCircle className="w-3.5 h-3.5" />}
                {activeJob.status || "Processing"}
              </span>

              {isCompleted && onNavigate && (
                <button
                  onClick={() => onNavigate('results')}
                  className="px-4 py-2 bg-[#005BAC] hover:bg-[#004787] text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  View Extracted Results
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Animated Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-bold text-slate-700">
              <span className="flex items-center gap-1.5 text-[#005BAC]">
                <Sparkles className="w-4 h-4" />
                Current Stage: {activeJob.current_stage || "Processing"}
              </span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden p-0.5 border border-slate-200">
              <div 
                className="h-full bg-gradient-to-r from-[#E60012] to-[#005BAC] rounded-full transition-all duration-500"
                style={{ width: `${Math.max(progress, 5)}%` }}
              ></div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 space-y-3">
          <Clock className="w-8 h-8 text-slate-400 mx-auto" />
          <h3 className="font-bold text-slate-800 text-sm">No Active Document Processing Session</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">Upload a document or image to view real-time stage execution and live pipeline telemetry.</p>
        </div>
      )}

      {/* Real Worker Logs Terminal */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-slate-700" />
            <h3 className="font-bold text-slate-900 text-sm">Real Execution Logs</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Live log stream</span>
        </div>

        <div className="bg-slate-950 text-slate-200 rounded-xl p-5 font-mono text-xs max-h-72 overflow-y-auto space-y-1.5">
          {activeJob && activeJob.logs && activeJob.logs.length > 0 ? (
            activeJob.logs.map((l: any, i: number) => (
              <div key={i} className="flex items-start gap-3 border-b border-slate-900 pb-1">
                <span className="text-slate-500 font-bold shrink-0">[{l.timestamp}]</span>
                <span className={`shrink-0 font-bold ${l.level === 'ERROR' ? 'text-red-400' : 'text-emerald-400'}`}>[{l.level}]</span>
                <span className="text-slate-300 leading-snug">{l.message}</span>
              </div>
            ))
          ) : logs.length > 0 ? (
            logs.map((l, i) => (
              <div key={i} className="flex items-start gap-3 border-b border-slate-900 pb-1">
                <span className="text-[#005BAC] font-bold shrink-0">[{l.worker}]</span>
                <span className="text-slate-300 leading-snug">{l.message}</span>
              </div>
            ))
          ) : (
            <div className="py-8 text-center text-slate-500 font-mono">
              Waiting for execution log entries...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
