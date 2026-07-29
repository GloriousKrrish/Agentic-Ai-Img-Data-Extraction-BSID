import React, { useState } from 'react';
import type { InvoiceRow } from '../types';
import { Search, Download, RefreshCw } from 'lucide-react';

interface ResultsProps {
  rows: InvoiceRow[];
  onRefresh: () => void;
}

export const Results: React.FC<ResultsProps> = ({ rows, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState<string>("");

  const filteredRows = rows.filter(r => 
    r.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.vehicleNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.dealerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.pattern.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const exportExcelFile = () => {
    const a = document.createElement("a");
    a.href = "/api/excel-rows";
    a.download = "Invoice_data_capture.xlsx";
    a.click();
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Live Excel View & Results</h2>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" title="Live Excel Sync"></span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">Real-time synchronized data grid from Invoice_data_capture.xlsx</p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={exportExcelFile}
            className="px-4 py-2 bg-[#005BAC] hover:bg-[#004787] text-white font-bold text-xs rounded-xl shadow-xs transition-all flex items-center gap-2 cursor-pointer"
          >
            <Download className="w-4 h-4" />
            Download Excel File
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
            placeholder="Search by customer, vehicle, pattern, dealer..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-slate-900 focus:outline-none focus:border-[#E60012]"
          />
        </div>

        <div className="text-xs font-semibold text-slate-600">
          Showing {filteredRows.length} of {rows.length} Total Rows
        </div>
      </div>

      {/* Live Excel Table Grid */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
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
                    <td className="py-3 px-4 font-semibold">{row.customerName || '-'}</td>
                    <td className="py-3 px-4">{row.customerMobile || '-'}</td>
                    <td className="py-3 px-4 font-mono uppercase font-bold text-slate-900">{row.vehicleNumber || '-'}</td>
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
                ))
              ) : (
                <tr>
                  <td colSpan={11} className="py-16 text-center text-slate-400 text-xs font-medium">
                    Waiting for backend data from Excel workbook...
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
