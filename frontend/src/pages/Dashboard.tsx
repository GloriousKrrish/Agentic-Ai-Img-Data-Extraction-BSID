import React from 'react';
import type { SystemKPIs, InvoiceRow } from '../types';
import { Upload, Table, Clock } from 'lucide-react';

interface DashboardProps {
  kpis: SystemKPIs;
  recentRows: InvoiceRow[];
  onNavigate: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ kpis, recentRows, onNavigate }) => {
  const isEngineActive = kpis.pendingInvoices > 0;

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Title & Engine Status */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-100 rounded-full text-xs font-bold text-slate-700 mb-2">
            Bridgestone Document Intelligence
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Bridgestone Agentic AI Data Extraction Engine
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time parallel pipeline for automated invoice data extraction and Excel synchronization.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 border ${
            isEngineActive 
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
              : 'bg-slate-100 text-slate-700 border-slate-200'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isEngineActive ? 'bg-emerald-500 animate-ping' : 'bg-slate-400'}`}></span>
            {isEngineActive ? 'Engine Processing Active' : 'Engine Idle'}
          </div>
        </div>
      </div>

      {/* Quick Action Navigation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div 
          onClick={() => onNavigate('upload')}
          className="bg-white border border-slate-200 hover:border-[#E60012] rounded-2xl p-6 shadow-xs hover:shadow-md transition-all cursor-pointer space-y-3"
        >
          <div className="w-10 h-10 rounded-xl bg-[#E600120D] text-[#E60012] flex items-center justify-center font-bold">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Upload Invoices</h3>
            <p className="text-xs text-slate-500 mt-0.5">Upload invoice images, PDFs, or Excel lists to begin</p>
          </div>
        </div>

        <div 
          onClick={() => onNavigate('processing')}
          className="bg-white border border-slate-200 hover:border-[#005BAC] rounded-2xl p-6 shadow-xs hover:shadow-md transition-all cursor-pointer space-y-3"
        >
          <div className="w-10 h-10 rounded-xl bg-[#005BAC0D] text-[#005BAC] flex items-center justify-center font-bold">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Live Processing Queue</h3>
            <p className="text-xs text-slate-500 mt-0.5">Monitor parallel workers, queue locks, and live logs</p>
          </div>
        </div>

        <div 
          onClick={() => onNavigate('results')}
          className="bg-white border border-slate-200 hover:border-emerald-600 rounded-2xl p-6 shadow-xs hover:shadow-md transition-all cursor-pointer space-y-3"
        >
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <Table className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Live Excel Sync Results</h3>
            <p className="text-xs text-slate-500 mt-0.5">View real-time extracted rows from Invoice_data_capture.xlsx</p>
          </div>
        </div>
      </div>

      {/* Real Recent Processing Jobs */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Recent Processing Rows</h3>
            <p className="text-xs text-slate-500">Real rows loaded directly from backend Excel sheet</p>
          </div>
          <span className="text-xs font-semibold text-slate-600">
            {kpis.processedInvoices} / {kpis.totalInvoices} Processed
          </span>
        </div>

        {recentRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-500 uppercase font-semibold">
                  <th className="py-2.5 px-3">Row #</th>
                  <th className="py-2.5 px-3">Customer Name</th>
                  <th className="py-2.5 px-3">Vehicle Plate</th>
                  <th className="py-2.5 px-3">Pattern</th>
                  <th className="py-2.5 px-3">Total Cost</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                {recentRows.slice(0, 6).map((row) => (
                  <tr key={row.rowIndex}>
                    <td className="py-2.5 px-3 font-bold text-[#005BAC]">#{row.rowIndex}</td>
                    <td className="py-2.5 px-3">{row.customerName || '-'}</td>
                    <td className="py-2.5 px-3 font-mono uppercase">{row.vehicleNumber || '-'}</td>
                    <td className="py-2.5 px-3 font-bold text-[#E60012]">{row.pattern || '-'}</td>
                    <td className="py-2.5 px-3 font-bold text-emerald-600">{row.totalCost ? `₹${row.totalCost}` : '-'}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        row.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                      }`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-400 text-xs font-medium">
            Waiting for backend data from Excel workbook...
          </div>
        )}
      </div>
    </div>
  );
};
