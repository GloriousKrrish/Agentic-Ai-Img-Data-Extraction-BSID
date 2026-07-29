import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Download, Eye, X, FileText } from 'lucide-react';
import type { InvoiceRow } from '../types';

interface ResultsProps {
  rows: InvoiceRow[];
}

export const Results: React.FC<ResultsProps> = ({ rows }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDealer, setSelectedDealer] = useState("ALL");
  const [activeRow, setActiveRow] = useState<InvoiceRow | null>(null);

  const dealers = Array.from(new Set(rows.map(r => r.dealerName).filter(Boolean)));

  const filteredRows = rows.filter(r => {
    const matchesSearch = 
      r.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.vehicleNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.pattern.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDealer = selectedDealer === "ALL" || r.dealerName === selectedDealer;
    return matchesSearch && matchesDealer;
  });

  const exportCSV = () => {
    const headers = ["RowIndex,CustomerName,CustomerMobile,VehicleNumber,Size,Pattern,DOT,Cost,TotalCost,DealerName\n"];
    const csvRows = filteredRows.map(r => 
      `"${r.rowIndex}","${r.customerName}","${r.customerMobile}","${r.vehicleNumber}","${r.size}","${r.pattern}","${r.dot}","${r.cost}","${r.totalCost}","${r.dealerName}"`
    ).join("\n");
    const blob = new Blob([headers + csvRows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bridgestone_extracted_invoices_${Date.now()}.csv`;
    a.click();
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-[#1B1B1B] tracking-tight">Results & Inspection Grid</h2>
          <p className="text-xs text-[#6B7280]">Search, filter, inspect, and export all extracted invoice records</p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={exportCSV}
            className="px-4 py-2.5 bg-[#005BAC] hover:bg-[#004787] text-white text-xs font-bold rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="glass-card rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-[#94A3B8] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input 
            type="text" 
            placeholder="Search customer, vehicle plate, pattern..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl text-xs font-semibold text-[#1E293B] focus:outline-none focus:border-[#005BAC]"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select 
            value={selectedDealer}
            onChange={(e) => setSelectedDealer(e.target.value)}
            className="px-3 py-2 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl text-xs font-semibold text-[#1E293B]"
          >
            <option value="ALL">All Dealers ({dealers.length})</option>
            {dealers.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Data Table */}
      <div className="glass-card rounded-2xl overflow-hidden shadow-xs">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#F8FAFC] border-b border-[#ECECEC] text-[#64748B] uppercase font-bold tracking-wider">
            <tr>
              <th className="py-3 px-4">Row #</th>
              <th className="py-3 px-4">Customer</th>
              <th className="py-3 px-4">Mobile</th>
              <th className="py-3 px-4">Vehicle Plate</th>
              <th className="py-3 px-4">Pattern</th>
              <th className="py-3 px-4">Tire Size</th>
              <th className="py-3 px-4">Total Price</th>
              <th className="py-3 px-4">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#ECECEC] font-medium text-[#1E293B]">
            {filteredRows.map(r => (
              <tr key={r.rowIndex} className="hover:bg-[#F8FAFC] transition-colors">
                <td className="py-3 px-4 font-bold text-[#005BAC]">#{r.rowIndex}</td>
                <td className="py-3 px-4 font-semibold">{r.customerName || 'N/A'}</td>
                <td className="py-3 px-4">{r.customerMobile || 'N/A'}</td>
                <td className="py-3 px-4 font-mono uppercase font-bold">{r.vehicleNumber || 'N/A'}</td>
                <td className="py-3 px-4 font-extrabold text-[#E60012]">{r.pattern || 'N/A'}</td>
                <td className="py-3 px-4">{r.size || 'N/A'}</td>
                <td className="py-3 px-4 font-bold text-emerald-600">₹{r.totalCost || '0.00'}</td>
                <td className="py-3 px-4">
                  <button 
                    onClick={() => setActiveRow(r)}
                    className="p-1.5 bg-[#005BAC10] hover:bg-[#005BAC20] text-[#005BAC] rounded-lg transition-colors"
                    title="Inspect Item"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail Modal Inspector */}
      <AnimatePresence>
        {activeRow && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl p-6 max-w-lg w-full space-y-5 shadow-2xl border border-[#ECECEC]"
            >
              <div className="flex items-center justify-between border-b border-[#ECECEC] pb-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-[#E60012]" />
                  <h3 className="font-extrabold text-[#1E293B]">Invoice Row #{activeRow.rowIndex} Inspector</h3>
                </div>
                <button onClick={() => setActiveRow(null)} className="p-1 text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 bg-slate-50 rounded-lg">
                  <span className="text-[#64748B] block font-semibold text-[10px]">Customer Name</span>
                  <span className="font-bold text-[#1E293B]">{activeRow.customerName || 'N/A'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg">
                  <span className="text-[#64748B] block font-semibold text-[10px]">Mobile</span>
                  <span className="font-bold text-[#005BAC]">{activeRow.customerMobile || 'N/A'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg">
                  <span className="text-[#64748B] block font-semibold text-[10px]">Vehicle Plate</span>
                  <span className="font-mono font-bold text-[#1E293B]">{activeRow.vehicleNumber || 'N/A'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg">
                  <span className="text-[#64748B] block font-semibold text-[10px]">Tire Size</span>
                  <span className="font-bold text-[#1E293B]">{activeRow.size || 'N/A'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg">
                  <span className="text-[#64748B] block font-semibold text-[10px]">Pattern</span>
                  <span className="font-extrabold text-[#E60012]">{activeRow.pattern || 'N/A'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 rounded-lg">
                  <span className="text-[#64748B] block font-semibold text-[10px]">DOT Code</span>
                  <span className="font-mono font-bold text-[#1E293B]">{activeRow.dot || 'N/A'}</span>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg text-xs">
                <span className="text-[#64748B] block font-semibold text-[10px]">Dealer Name</span>
                <span className="font-bold text-[#1E293B]">{activeRow.dealerName || 'N/A'}</span>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
