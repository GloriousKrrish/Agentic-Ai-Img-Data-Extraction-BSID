import React, { useState } from 'react';
import type { UniversalDocumentDataset } from '../types';
import { Search, Download, RefreshCw, CheckCircle2 } from 'lucide-react';
import { getApiUrl } from '../config/api';

interface ResultsProps {
  dataset: UniversalDocumentDataset;
  onRefresh: () => void;
  activeJob?: any | null;
  allJobs?: any[];
  onSelectJob?: (jobId: string) => void;
}

export const Results: React.FC<ResultsProps> = ({ 
  dataset, 
  onRefresh,
  activeJob,
  allJobs = [],
  onSelectJob
}) => {
  const [searchTerm, setSearchTerm] = useState<string>("");

  const activeSchema = activeJob?.schema && activeJob.schema.length > 0 ? activeJob.schema : dataset?.schema || [];
  const activeRows = activeJob?.rows && activeJob.rows.length > 0 ? activeJob.rows : dataset?.rows || [];

  const filteredRows = activeRows.filter((r: any) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return Object.values(r.fields || {}).some(val => 
      String(val || '').toLowerCase().includes(term)
    );
  });

  const downloadFormat = (format: 'excel' | 'csv' | 'json') => {
    const jobId = activeJob?.job_id;
    let targetUrl = getApiUrl('/api/excel-rows');
    if (jobId) {
      targetUrl = getApiUrl(`/api/jobs/${jobId}/download/${format}`);
    }
    const a = document.createElement("a");
    a.href = targetUrl;
    a.download = `extracted_results_${jobId || 'export'}.${format === 'excel' ? 'xlsx' : format}`;
    a.click();
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Dynamic Data Grid & Results</h2>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" title="Live Dynamic Sync"></span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">Real-time synchronized data grid constructed dynamically from backend schema</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Job Selector Dropdown */}
          {allJobs.length > 0 && onSelectJob && (
            <div className="relative">
              <select
                value={activeJob?.job_id || ""}
                onChange={(e) => onSelectJob(e.target.value)}
                className="px-3 py-2 bg-white border border-slate-300 text-slate-800 text-xs font-bold rounded-xl focus:outline-none focus:border-[#005BAC]"
              >
                {allJobs.map((j) => (
                  <option key={j.job_id} value={j.job_id}>
                    {j.filename} ({j.job_id}) — {j.status}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button 
            onClick={() => downloadFormat('excel')}
            className="px-4 py-2 bg-[#005BAC] hover:bg-[#004787] text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center gap-2 cursor-pointer"
          >
            <Download className="w-4 h-4" />
            Download Excel (.xlsx)
          </button>

          <button 
            onClick={() => downloadFormat('csv')}
            className="px-3 py-2 bg-slate-100 border border-slate-200 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all flex items-center gap-1.5 cursor-pointer"
          >
            CSV
          </button>

          <button 
            onClick={() => downloadFormat('json')}
            className="px-3 py-2 bg-slate-100 border border-slate-200 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all flex items-center gap-1.5 cursor-pointer"
          >
            JSON
          </button>

          <button 
            onClick={onRefresh}
            className="p-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl cursor-pointer"
            title="Refresh Rows"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Active Job Information Banner */}
      {activeJob && (
        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-50 text-emerald-700 rounded-lg">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-slate-900 text-sm">{activeJob.filename}</span>
                <span className="text-xs text-slate-400 font-mono">({activeJob.job_id})</span>
              </div>
              <p className="text-xs text-slate-500">Category: {activeJob.document_category || "Universal Document"} · Status: {activeJob.status}</p>
            </div>
          </div>

          <div className="text-xs font-bold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
            {activeRows.length} Rows · {activeSchema.length} Schema Columns
          </div>
        </div>
      )}

      {/* Search & Counter Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-xs">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input 
            type="text" 
            placeholder="Search across all dynamic columns..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-slate-900 focus:outline-none focus:border-[#E60012]"
          />
        </div>

        <div className="text-xs font-semibold text-slate-600">
          Showing {filteredRows.length} of {activeRows.length} Total Rows ({activeSchema.length} Discovered Columns)
        </div>
      </div>

      {/* Live Dynamic Table Grid */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto max-h-[600px]">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-slate-900 text-white z-10 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Row #</th>
                {activeSchema.map((col: any) => (
                  <th key={col.key} className="py-3.5 px-4 whitespace-nowrap">
                    {col.label}
                  </th>
                ))}
                <th className="py-3.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
              {filteredRows.length > 0 ? (
                filteredRows.map((row: any) => (
                  <tr 
                    key={row.rowIndex} 
                    className={`hover:bg-slate-50 transition-colors ${
                      row.status === 'COMPLETED' ? 'bg-white' : 'bg-slate-50/60'
                    }`}
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-400">
                      #{row.rowIndex}
                    </td>
                    {activeSchema.map((col: any) => (
                      <td key={col.key} className="py-3.5 px-4 whitespace-nowrap">
                        {row.fields && row.fields[col.key] !== undefined && row.fields[col.key] !== null ? (
                          String(row.fields[col.key]).startsWith("http") ? (
                            <a
                              href={String(row.fields[col.key])}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#005BAC] underline font-bold"
                            >
                              View Link
                            </a>
                          ) : (
                            String(row.fields[col.key])
                          )
                        ) : (
                          <span className="text-slate-300 font-normal">-</span>
                        )}
                      </td>
                    ))}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                        row.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {row.status || 'COMPLETED'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={activeSchema.length + 2} className="py-12 text-center text-slate-400 font-semibold">
                    No matching records found. Upload a document or dataset to view dynamic extraction results.
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
