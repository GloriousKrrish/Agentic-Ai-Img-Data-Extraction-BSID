import React, { useState } from 'react';
import type { JobRecord } from '../types';
import { Search, Download, RefreshCw, Loader2, CheckCircle2, AlertCircle, FileText, Trash2 } from 'lucide-react';

interface ResultsProps {
  jobs: JobRecord[];
  activeJobId?: string | null;
  onSelectJob?: (jobId: string) => void;
  onRefresh: () => void;
  onDeleteJob?: (jobId: string) => void;
}

export const Results: React.FC<ResultsProps> = ({ 
  jobs, 
  activeJobId, 
  onSelectJob, 
  onRefresh,
  onDeleteJob 
}) => {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedJobId, setSelectedJobId] = useState<string | null>(
    activeJobId || localStorage.getItem("current_active_job_id") || (jobs.length > 0 ? jobs[0].job_id : null)
  );

  const activeJob = jobs.find(j => j.job_id === (selectedJobId || activeJobId)) || (jobs.length > 0 ? jobs[0] : null);

  const schema = activeJob?.schema || [];
  const rows = activeJob?.rows || [];

  const filteredRows = rows.filter(r => {
    if (!searchTerm.trim()) return true;
    if (!r.fields) return false;
    return Object.values(r.fields).some(val => 
      String(val || '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const handleDownload = (format: 'excel' | 'json' | 'csv') => {
    if (!activeJob) return;
    const a = document.createElement("a");
    a.href = `/api/jobs/${activeJob.job_id}/download/${format}`;
    a.download = `${activeJob.job_id}_results.${format === 'excel' ? 'xlsx' : format}`;
    a.click();
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Page Header & Backend Job Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Persistent Job Results & Data Grid</h2>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" title="Backend Live Sync"></span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">100% Backend-Owned Execution — SQLite Store (`jobs.sqlite3`)</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Job Dropdown Selector */}
          {jobs.length > 0 && (
            <select
              value={activeJob?.job_id || ""}
              onChange={(e) => {
                setSelectedJobId(e.target.value);
                localStorage.setItem("current_active_job_id", e.target.value);
                if (onSelectJob) onSelectJob(e.target.value);
              }}
              className="px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs font-bold text-slate-800 shadow-xs focus:outline-none focus:border-[#E60012]"
            >
              {jobs.map(j => (
                <option key={j.job_id} value={j.job_id}>
                  {j.filename} ({j.status} - {j.progress.toFixed(0)}%) [{j.job_id}]
                </option>
              ))}
            </select>
          )}

          {activeJob && (
            <button 
              onClick={() => handleDownload('excel')}
              className="px-4 py-2 bg-[#005BAC] hover:bg-[#004787] text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center gap-2 cursor-pointer"
            >
              <Download className="w-4 h-4" />
              Download Excel
            </button>
          )}

          <button 
            onClick={onRefresh}
            className="p-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl"
            title="Refresh Jobs from Backend"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Active Job Progress & Stage Telemetry Card */}
      {activeJob && (
        <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-[#005BAC]" />
                <span className="font-extrabold text-sm text-white">{activeJob.filename}</span>
                <span className="text-xs text-slate-400 font-mono">({activeJob.job_id})</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Category: <strong className="text-emerald-400">{activeJob.document_category || 'Detecting...'}</strong> | Created: {activeJob.created_at}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-xs font-black flex items-center gap-1.5 ${
                activeJob.status === 'Completed' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                activeJob.status === 'Failed' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                'bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse'
              }`}>
                {activeJob.status === 'Completed' ? <CheckCircle2 className="w-3.5 h-3.5" /> :
                 activeJob.status === 'Failed' ? <AlertCircle className="w-3.5 h-3.5" /> :
                 <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                {activeJob.status}
              </span>

              {onDeleteJob && (
                <button 
                  onClick={() => onDeleteJob(activeJob.job_id)}
                  className="p-1.5 text-slate-400 hover:text-red-400 rounded-lg hover:bg-slate-800"
                  title="Delete Job Record"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-bold">
              <span className="text-slate-300 flex items-center gap-2">
                {activeJob.status !== 'Completed' && activeJob.status !== 'Failed' && (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[#E60012]" />
                )}
                Stage: {activeJob.current_stage}
              </span>
              <span className="text-emerald-400 font-mono">{activeJob.progress.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div 
                className="bg-gradient-to-r from-[#005BAC] to-emerald-500 h-full transition-all duration-500"
                style={{ width: `${Math.max(activeJob.progress, 5)}%` }}
              ></div>
            </div>
          </div>

          {/* Job Logs */}
          {activeJob.logs && activeJob.logs.length > 0 && (
            <div className="bg-slate-950 rounded-xl p-3 font-mono text-[11px] max-h-28 overflow-y-auto space-y-1 text-slate-300">
              {activeJob.logs.slice(-4).map((l, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="text-slate-500 text-[10px]">{l.timestamp}</span>
                  <span className={l.level === 'ERROR' ? 'text-red-400 font-bold' : l.level === 'SUCCESS' ? 'text-emerald-400 font-bold' : 'text-slate-300'}>
                    {l.message}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Search & Counter Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-xs">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input 
            type="text" 
            placeholder="Search across all extracted fields..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-slate-900 focus:outline-none focus:border-[#E60012]"
          />
        </div>

        <div className="text-xs font-semibold text-slate-600">
          Showing {filteredRows.length} of {rows.length} Total Rows | {schema.length} Auto-Discovered Columns
        </div>
      </div>

      {/* Dynamic Data Grid */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto max-h-[600px]">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-slate-900 text-white z-10 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4 shrink-0">Row #</th>
                {schema.map((col) => (
                  <th key={col.key} className="py-3.5 px-4 whitespace-nowrap">
                    {col.label}
                  </th>
                ))}
                <th className="py-3.5 px-4 shrink-0">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
              {filteredRows.length > 0 ? (
                filteredRows.map((row) => (
                  <tr 
                    key={row.rowIndex} 
                    className={`hover:bg-slate-50 transition-colors ${
                      row.status === 'COMPLETED' ? 'bg-white' : 'bg-slate-50/60'
                    }`}
                  >
                    <td className="py-3 px-4 font-bold text-[#005BAC] whitespace-nowrap">#{row.rowIndex}</td>
                    {schema.map((col) => (
                      <td key={col.key} className="py-3 px-4 max-w-xs truncate">
                        {row.fields && row.fields[col.key] !== undefined && row.fields[col.key] !== null && String(row.fields[col.key]).trim() !== ''
                          ? String(row.fields[col.key])
                          : '-'}
                      </td>
                    ))}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold ${
                        row.status === 'COMPLETED' 
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={Math.max(schema.length + 2, 1)} className="py-16 text-center text-slate-400 text-xs font-medium">
                    {activeJob && activeJob.status !== 'Completed' && activeJob.status !== 'Failed' ? (
                      <div className="flex flex-col items-center gap-2">
                        <Loader2 className="w-6 h-6 animate-spin text-[#E60012]" />
                        <span>Background AI Worker is extracting data ({activeJob.progress.toFixed(0)}%)...</span>
                      </div>
                    ) : (
                      "No data rows loaded. Upload a document to create a persistent job."
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
