import React, { useState } from 'react';
import type { UniversalDocumentDataset } from '../types';
import { Search, Download, RefreshCw, Table as TableIcon } from 'lucide-react';

interface ResultsProps {
  dataset: UniversalDocumentDataset;
  onRefresh: () => void;
}

export const Results: React.FC<ResultsProps> = ({ dataset, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState<string>("");

  const schema = dataset?.schema || [];
  const rows = dataset?.rows || [];

  const filteredRows = rows.filter(r => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return Object.values(r.fields || {}).some(val => 
      String(val || '').toLowerCase().includes(term)
    );
  });

  const exportExcelFile = () => {
    const a = document.createElement("a");
    a.href = "/api/excel-rows";
    a.download = "extracted_data.xlsx";
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
          <button 
            onClick={exportExcelFile}
            className="px-4 py-2 bg-[#005BAC] hover:bg-[#004787] text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center gap-2 cursor-pointer"
          >
            <Download className="w-4 h-4" />
            Export Dynamic Excel
          </button>
          <button 
            onClick={onRefresh}
            className="p-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl"
            title="Refresh Rows"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

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
          Showing {filteredRows.length} of {rows.length} Total Rows ({schema.length} Auto-Discovered Columns)
        </div>
      </div>

      {/* Live Dynamic Table Grid */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto max-h-[600px]">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-slate-900 text-white z-10 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Row #</th>
                {schema.map(col => (
                  <th key={col.key} className="py-3.5 px-4 whitespace-nowrap">
                    {col.label}
                  </th>
                ))}
                <th className="py-3.5 px-4">Status</th>
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
                    <td className="py-3 px-4 font-bold text-[#005BAC]">#{row.rowIndex}</td>
                    {schema.map(col => (
                      <td key={col.key} className="py-3 px-4">
                        {String(row.fields[col.key] || '-')}
                      </td>
                    ))}
                    <td className="py-3 px-4">
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
                  <td colSpan={schema.length + 2} className="py-16 text-center text-slate-400 text-xs font-medium">
                    <TableIcon className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                    Waiting for dataset upload or backend processing stream...
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
