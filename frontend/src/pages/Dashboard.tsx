import React from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Cpu, 
  Clock, 
  CheckCircle2, 
  Zap, 
  TrendingUp, 
  Sparkles, 
  Layers, 
  ShieldCheck,
  ArrowUpRight
} from 'lucide-react';
import type { SystemKPIs, WorkerNode, InvoiceRow } from '../types';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface DashboardProps {
  kpis: SystemKPIs;
  workers: WorkerNode[];
  recentRows: InvoiceRow[];
  onNavigate: (tab: string) => void;
}

const chartData = [
  { time: '09:00', invoices: 12, speed: 2.1 },
  { time: '10:00', invoices: 24, speed: 2.4 },
  { time: '11:00', invoices: 45, speed: 2.3 },
  { time: '12:00', invoices: 68, speed: 2.5 },
  { time: '13:00', invoices: 82, speed: 2.2 },
  { time: '14:00', invoices: 110, speed: 2.6 },
  { time: '15:00', invoices: 142, speed: 2.4 },
  { time: '16:00', invoices: 175, speed: 2.7 },
  { time: '17:00', invoices: 215, speed: 2.5 },
];

export const Dashboard: React.FC<DashboardProps> = ({ kpis, workers, recentRows, onNavigate }) => {
  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Hero Section */}
      <motion.div 
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white rounded-2xl p-8 shadow-xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#E6001215] rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none"></div>
        <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-[#005BAC15] rounded-full blur-3xl -mb-20 pointer-events-none"></div>
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 backdrop-blur-md rounded-full text-xs font-semibold text-white/90 border border-white/15">
              <Sparkles className="w-3.5 h-3.5 text-[#E60012]" />
              Enterprise Document Intelligence Platform
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight text-white">
              Bridgestone Agentic AI Data Extraction Engine
            </h2>
            <p className="text-sm text-slate-300 max-w-2xl font-normal leading-relaxed">
              High-throughput multimodal AI pipeline powered by Google Gemini 3.5 & 2.5 Flash for automated tire invoice extraction, handwritten OCR sanitization, and live Excel synchronization.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={() => onNavigate('invoice-processing')}
              className="px-5 py-3 bg-[#E60012] hover:bg-[#C2000F] text-white font-semibold text-xs rounded-xl shadow-lg hover:shadow-red-900/30 transition-all flex items-center gap-2 cursor-pointer"
            >
              <FileText className="w-4 h-4" />
              Upload Invoice
            </button>
            <button 
              onClick={() => onNavigate('batch-processing')}
              className="px-5 py-3 bg-white/10 hover:bg-white/20 text-white font-semibold text-xs rounded-xl border border-white/20 transition-all flex items-center gap-2 cursor-pointer"
            >
              <Layers className="w-4 h-4 text-[#005BAC]" />
              Launch Batch Engine
            </button>
          </div>
        </div>
      </motion.div>

      {/* Live KPIs Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <motion.div 
          whileHover={{ y: -3 }}
          className="glass-card rounded-2xl p-5 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#6B7280] uppercase tracking-wider">Invoices Processed</span>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-[#1B1B1B] tracking-tight">{kpis.processedInvoices}</div>
            <div className="text-xs text-emerald-600 font-semibold mt-1 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" />
              {kpis.successRate}% Success Rate
            </div>
          </div>
        </motion.div>

        <motion.div 
          whileHover={{ y: -3 }}
          className="glass-card rounded-2xl p-5 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#6B7280] uppercase tracking-wider">Pending Queue</span>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-[#1B1B1B] tracking-tight">{kpis.pendingInvoices}</div>
            <div className="text-xs text-[#6B7280] font-medium mt-1">
              Out of {kpis.totalInvoices} total rows
            </div>
          </div>
        </motion.div>

        <motion.div 
          whileHover={{ y: -3 }}
          className="glass-card rounded-2xl p-5 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#6B7280] uppercase tracking-wider">Avg Confidence</span>
            <div className="w-10 h-10 rounded-xl bg-[#005BAC10] text-[#005BAC] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-[#1B1B1B] tracking-tight">{kpis.avgConfidence}%</div>
            <div className="text-xs text-[#005BAC] font-semibold mt-1 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" />
              High precision JSON
            </div>
          </div>
        </motion.div>

        <motion.div 
          whileHover={{ y: -3 }}
          className="glass-card rounded-2xl p-5 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#6B7280] uppercase tracking-wider">Gemini Requests</span>
            <div className="w-10 h-10 rounded-xl bg-[#E6001210] text-[#E60012] flex items-center justify-center">
              <Zap className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-[#1B1B1B] tracking-tight">{kpis.geminiRequests}</div>
            <div className="text-xs text-[#6B7280] font-medium mt-1">
              Avg latency: {kpis.avgProcessingTime}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Main Grid: Live Analytics Chart & Active Workers */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Analytics Trend Chart */}
        <div className="lg:col-span-2 glass-card rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-[#1B1B1B]">Invoice Processing Throughput</h3>
              <p className="text-xs text-[#6B7280]">Real-time hourly invoice extraction trend</p>
            </div>
            <span className="text-xs font-bold px-2.5 py-1 bg-[#005BAC10] text-[#005BAC] rounded-full">
              Live Stream
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorInvoices" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#E60012" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#E60012" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="time" stroke="#94A3B8" fontSize={11} />
                <YAxis stroke="#94A3B8" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#ECECEC', borderRadius: '12px', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)' }}
                  labelStyle={{ fontWeight: 'bold', color: '#1B1B1B' }}
                />
                <Area type="monotone" dataKey="invoices" stroke="#E60012" strokeWidth={3} fillOpacity={1} fill="url(#colorInvoices)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Worker Node Quick Status */}
        <div className="glass-card rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#ECECEC] pb-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#E60012]" />
              <h3 className="text-base font-bold text-[#1B1B1B]">Active Worker Nodes</h3>
            </div>
            <button 
              onClick={() => onNavigate('live-queue')} 
              className="text-xs text-[#005BAC] font-semibold hover:underline flex items-center gap-0.5 cursor-pointer"
            >
              View Queue <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {workers.map((worker) => (
              <div key={worker.id} className="p-3 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0] space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#1E293B]">{worker.name}</span>
                  <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                    worker.status === 'RUNNING' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-700'
                  }`}>
                    {worker.status}
                  </span>
                </div>
                <div className="text-[11px] text-[#64748B] flex items-center justify-between">
                  <span>Task: {worker.currentTask}</span>
                  <span className="font-medium text-[#005BAC]">{worker.modelUsed}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Extraction Live Feed */}
      <div className="glass-card rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-[#ECECEC] pb-4">
          <div>
            <h3 className="text-base font-bold text-[#1B1B1B]">Recent Extracted Invoices</h3>
            <p className="text-xs text-[#6B7280]">Live feed of extracted metadata from Excel sheet</p>
          </div>
          <button 
            onClick={() => onNavigate('excel-sync')}
            className="px-4 py-2 bg-slate-900 hover:bg-black text-white text-xs font-semibold rounded-xl transition-all cursor-pointer"
          >
            Open Live Excel Sync Grid
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#ECECEC] text-[#6B7280] uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Row #</th>
                <th className="py-3 px-4">Customer Name</th>
                <th className="py-3 px-4">Mobile</th>
                <th className="py-3 px-4">Vehicle No</th>
                <th className="py-3 px-4">Tire Size</th>
                <th className="py-3 px-4">Pattern</th>
                <th className="py-3 px-4">Total Cost</th>
                <th className="py-3 px-4">Dealer Name</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#ECECEC] font-medium text-[#1B1B1B]">
              {recentRows.slice(0, 5).map((row) => (
                <tr key={row.rowIndex} className="hover:bg-[#F8FAFC] transition-colors">
                  <td className="py-3 px-4 font-bold text-[#005BAC]">#{row.rowIndex}</td>
                  <td className="py-3 px-4">{row.customerName || 'N/A'}</td>
                  <td className="py-3 px-4">{row.customerMobile || 'N/A'}</td>
                  <td className="py-3 px-4 font-mono uppercase">{row.vehicleNumber || 'N/A'}</td>
                  <td className="py-3 px-4">{row.size || 'N/A'}</td>
                  <td className="py-3 px-4 font-bold">{row.pattern || 'N/A'}</td>
                  <td className="py-3 px-4 font-extrabold text-emerald-600">
                    {row.totalCost ? `₹${row.totalCost}` : 'N/A'}
                  </td>
                  <td className="py-3 px-4">{row.dealerName || 'N/A'}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                      row.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
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
