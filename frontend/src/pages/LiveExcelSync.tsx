import React, { useState } from 'react';
import { Search, RefreshCw } from 'lucide-react';
import type { InvoiceRow } from '../types';

interface LiveExcelSyncProps {
  rows: InvoiceRow[];
  onRefresh: () => void;
}

export const LiveExcelSync: React.FC<LiveExcelSyncProps> = ({ rows, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [autoScroll, setAutoScroll] = useState<boolean>(true);

  const filteredRows = rows.filter(r => 
    r.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.vehicleNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.dealerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.pattern.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-extrabold text-[#1B1B1B] tracking-tight">Live Excel Synchronization Grid</h2>
            <span className="w-2.5 h-2.5 rounded-full bg-[#E60012] animate-ping" title="Live Sync Active"></span>
          </div>
          <p className="text-xs text-[#6B7280]">Direct COM & OpenPyXL Excel row stream from master.ps1 execution</p>
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
            placeholder="Search by customer, vehicle, pattern, dealer..." 
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
                <th className="py-3.5 px-4">Customer Name</th>
                <th className="py-3.5 px-4">Mobile</th>
                <th className="py-3.5 px-4">Vehicle Plate</th>
                <th className="py-3.5 px-4">Tire Size</th>
                <th className="py-3.5 px-4">Pattern</th>
                <th className="py-3.5 px-4">DOT Code</th>
                <th className="py-3.5 px-4">Unit Cost</th>
                <th className="py-3.5 px-4">Total Cost</th>
                <th className="py-3.5 px-4">Dealer Name</th>
                <th className="py-3.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#ECECEC] font-medium text-[#1E293B]">
              {filteredRows.map((row) => (
                <tr 
                  key={row.rowIndex} 
                  className={`hover:bg-[#F8FAFC] transition-colors ${row.status === 'COMPLETED' ? 'bg-white' : 'bg-slate-50/50'}`}
                >
                  <td className="py-3 px-4 font-bold text-[#005BAC]">#{row.rowIndex}</td>
                  <td className="py-3 px-4 font-semibold">{row.customerName || '-'}</td>
                  <td className="py-3 px-4">{row.customerMobile || '-'}</td>
                  <td className="py-3 px-4 font-mono uppercase font-bold text-slate-800">{row.vehicleNumber || '-'}</td>
                  <td className="py-3 px-4">{row.size || '-'}</td>
                  <td className="py-3 px-4 font-bold text-[#E60012]">{row.pattern || '-'}</td>
                  <td className="py-3 px-4 font-mono">{row.dot || '-'}</td>
                  <td className="py-3 px-4">{row.cost ? `₹${row.cost}` : '-'}</td>
                  <td className="py-3 px-4 font-extrabold text-emerald-600">
                    {row.totalCost ? `₹${row.totalCost}` : '-'}
                  </td>
                  <td className="py-3 px-4">{row.dealerName || '-'}</td>
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
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
