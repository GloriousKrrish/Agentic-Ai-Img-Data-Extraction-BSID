import React, { useState } from 'react';
import { Search, RefreshCw, Table as TableIcon } from 'lucide-react';
import type { UniversalDocumentDataset } from '../types';

interface LiveExcelSyncProps {
  dataset: UniversalDocumentDataset;
  onRefresh: () => void;
}

export const LiveExcelSync: React.FC<LiveExcelSyncProps> = ({ dataset, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [autoScroll, setAutoScroll] = useState<boolean>(true);

  const schema = dataset?.schema || [];
  const rows = dataset?.rows || [];

  const filteredRows = rows.filter(r => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return Object.values(r.fields || {}).some(val => 
      String(val || '').toLowerCase().includes(term)
    );
  });

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-extrabold text-[#1B1B1B] tracking-tight">Live Dynamic Spreadsheet Sync Grid</h2>
            <span className="w-2.5 h-2.5 rounded-full bg-[#E60012] animate-ping" title="Live Sync Active"></span>
          </div>
          <p className="text-xs text-[#6B7280]">Direct spreadsheet row stream & dynamic column renderer</p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              autoScroll ? 'bg-[#005BAC] text-white' : 'bg-slate-100 text-slate-600'
            }`}
          >
            {autoScroll ? 'Auto-Scroll Active' : 'Auto-Scroll Off'}
          </button>
          <button 
            onClick={onRefresh}
            className="p-2 bg-white border border-[#ECECEC] hover:bg-slate-50 text-slate-700 rounded-xl"
            title="Reload Workbook Data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-card rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-[#94A3B8] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input 
            type="text" 
            placeholder="Search all dynamic columns..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl text-xs font-semibold text-[#1E293B] focus:outline-none focus:border-[#E60012]"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-[#64748B]">
          <span>Showing {filteredRows.length} of {rows.length} Rows</span>
        </div>
      </div>

      {/* Synchronized Datagrid */}
      <div className="glass-card rounded-2xl overflow-hidden shadow-xs">
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
            <tbody className="divide-y divide-[#ECECEC] font-medium text-[#1E293B]">
              {filteredRows.length > 0 ? (
                filteredRows.map((row) => (
                  <tr 
                    key={row.rowIndex} 
                    className={`hover:bg-[#F8FAFC] transition-colors ${row.status === 'COMPLETED' ? 'bg-white' : 'bg-slate-50/50'}`}
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
                    Waiting for dynamic spreadsheet stream...
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
