import React from 'react';
import type { SystemKPIs, UniversalDocumentDataset } from '../types';
import { Upload, Table, Clock, Sparkles } from 'lucide-react';

interface DashboardProps {
  kpis: SystemKPIs;
  dataset: UniversalDocumentDataset;
  onNavigate: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ kpis, dataset, onNavigate }) => {
  const isEngineActive = kpis.pendingDocuments > 0;
  const schema = dataset?.schema || [];
  const rows = dataset?.rows || [];

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Title & Engine Status */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#E6001210] text-[#E60012] border border-[#E6001220] rounded-full text-xs font-bold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            Universal AI Document Intelligence Platform (IDP)
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Universal AI Document Intelligence Platform
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Multimodal AI engine for real-time document classification, dynamic schema generation, and multi-format extraction.
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
            <h3 className="font-bold text-slate-900 text-sm">Drop Anything Here</h3>
            <p className="text-xs text-slate-500 mt-0.5">Upload PDFs, Images, Word, Excel, CSV, JSON, XML, or ZIP archives</p>
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
            <h3 className="font-bold text-slate-900 text-sm">Live Pipeline Inspector</h3>
            <p className="text-xs text-slate-500 mt-0.5">Monitor real-time AI classification, OCR & dynamic schema inference</p>
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
            <h3 className="font-bold text-slate-900 text-sm">Dynamic Results Grid</h3>
            <p className="text-xs text-slate-500 mt-0.5">View & export auto-generated table schemas across documents</p>
          </div>
        </div>
      </div>

      {/* Dynamic Extracted Document Stream */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Dynamic Document Dataset Stream</h3>
            <p className="text-xs text-slate-500">Auto-discovered schema columns & live extracted data rows</p>
          </div>
          <span className="text-xs font-semibold text-slate-600">
            {kpis.processedDocuments} / {kpis.totalDocuments} Documents Processed
          </span>
        </div>

        {rows.length > 0 && schema.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-500 uppercase font-semibold">
                  <th className="py-2.5 px-3">Row #</th>
                  {schema.slice(0, 5).map(col => (
                    <th key={col.key} className="py-2.5 px-3 whitespace-nowrap">
                      {col.label}
                    </th>
                  ))}
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                {rows.slice(0, 6).map((row) => (
                  <tr key={row.rowIndex}>
                    <td className="py-2.5 px-3 font-bold text-[#005BAC]">#{row.rowIndex}</td>
                    {schema.slice(0, 5).map(col => (
                      <td key={col.key} className="py-2.5 px-3">
                        {String(row.fields[col.key] || '-')}
                      </td>
                    ))}
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
            Waiting for backend document dataset stream...
          </div>
        )}
      </div>
    </div>
  );
};
