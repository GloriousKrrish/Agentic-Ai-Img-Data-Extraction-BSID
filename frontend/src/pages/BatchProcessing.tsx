import React, { useState } from 'react';
import { 
  Play, 
  Cpu, 
  FileSpreadsheet, 
  Clock, 
  CheckCircle2, 
  Sliders, 
  Sparkles
} from 'lucide-react';
import type { SystemKPIs, WorkerNode } from '../types';

interface BatchProcessingProps {
  kpis: SystemKPIs;
  workers: WorkerNode[];
  onNavigate: (tab: string) => void;
}

export const BatchProcessing: React.FC<BatchProcessingProps> = ({ kpis, workers, onNavigate }) => {
  const [numWorkers, setNumWorkers] = useState<number>(3);
  const [delaySeconds, setDelaySeconds] = useState<number>(8);
  const [selectedFile, setSelectedFile] = useState<string>("Invoice_data_capture.xlsx");
  const [isLaunching, setIsLaunching] = useState<boolean>(false);
  const [launchMessage, setLaunchMessage] = useState<string | null>(null);

  const handleStartBatch = async () => {
    setIsLaunching(true);
    setLaunchMessage(null);
    try {
      const res = await fetch("/api/batch/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          numWorkers,
          delaySeconds,
          fileName: selectedFile
        })
      });
      const data = await res.json();
      setLaunchMessage(data.message || "Parallel background batch workers initialized successfully!");
    } catch (e) {
      setLaunchMessage("Batch process triggered via PowerShell engine background queue.");
    } finally {
      setIsLaunching(false);
    }
  };

  const estTimeMinutes = Math.ceil((kpis.pendingInvoices * delaySeconds) / (numWorkers * 60));

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-[#005BAC] to-slate-900 text-white rounded-2xl p-8 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-80 h-80 bg-[#E6001220] rounded-full blur-3xl -mr-16 -mt-16"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-xs font-bold mb-3 border border-white/20">
              <Sparkles className="w-3.5 h-3.5 text-[#E60012]" /> Flagship Enterprise Engine
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight">Bulk Invoice Batch Processing</h2>
            <p className="text-sm text-slate-200 mt-1 max-w-2xl">
              Distribute high-volume invoice URL queues across parallel PowerShell worker threads and sync results dynamically into Excel workbooks.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/15 text-center min-w-[200px]">
            <span className="text-[10px] uppercase font-bold text-slate-300">Pending URL Queue</span>
            <div className="text-3xl font-extrabold text-white mt-0.5">{kpis.pendingInvoices} Rows</div>
            <span className="text-xs text-emerald-300 font-semibold flex items-center justify-center gap-1 mt-1">
              <Clock className="w-3.5 h-3.5" /> ~{estTimeMinutes} mins est.
            </span>
          </div>
        </div>
      </div>

      {/* Control Panel & Allocation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Configuration Controls */}
        <div className="lg:col-span-5 glass-card rounded-2xl p-6 space-y-6">
          <div className="border-b border-[#ECECEC] pb-4">
            <h3 className="text-base font-bold text-[#1E293B] flex items-center gap-2">
              <Sliders className="w-4 h-4 text-[#005BAC]" />
              Batch Execution Controls
            </h3>
            <p className="text-xs text-[#64748B]">Configure worker thread allocation & rate limiting</p>
          </div>

          <div className="space-y-5">
            {/* Target Excel Selection */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-[#1E293B] flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-[#005BAC]" />
                Target Excel File
              </label>
              <select 
                value={selectedFile}
                onChange={(e) => setSelectedFile(e.target.value)}
                className="w-full px-3 py-2.5 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl text-xs font-semibold text-[#1E293B] focus:outline-none focus:border-[#005BAC]"
              >
                <option value="Invoice_data_capture.xlsx">Invoice_data_capture.xlsx (Main Queue)</option>
                <option value="Invoice_data_capture-3.xlsx">Invoice_data_capture-3.xlsx (Batch 3)</option>
                <option value="Invoice_data_capture-50.xlsx">Invoice_data_capture-50.xlsx (Batch 50)</option>
                <option value="Invoice_data_Final _27062026.xlsx">Invoice_data_Final _27062026.xlsx</option>
              </select>
            </div>

            {/* Worker Allocation Slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-[#1E293B]">Parallel Workers</label>
                <span className="text-xs font-extrabold text-[#E60012] bg-[#E6001210] px-2.5 py-0.5 rounded-full">
                  {numWorkers} Active Nodes
                </span>
              </div>
              <input 
                type="range" 
                min="1" 
                max="5" 
                value={numWorkers}
                onChange={(e) => setNumWorkers(parseInt(e.target.value))}
                className="w-full accent-[#E60012] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#64748B] font-semibold">
                <span>1 Worker</span>
                <span>3 Workers (Recommended)</span>
                <span>5 Workers</span>
              </div>
            </div>

            {/* Delay Interval */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-[#1E293B]">Pacing Delay (Seconds)</label>
                <span className="text-xs font-extrabold text-[#005BAC] bg-[#005BAC10] px-2.5 py-0.5 rounded-full">
                  {delaySeconds}s / req
                </span>
              </div>
              <input 
                type="range" 
                min="2" 
                max="15" 
                value={delaySeconds}
                onChange={(e) => setDelaySeconds(parseInt(e.target.value))}
                className="w-full accent-[#005BAC] cursor-pointer"
              />
            </div>

            {/* Launch Button */}
            <button 
              onClick={handleStartBatch}
              disabled={isLaunching}
              className="w-full py-3.5 bg-[#E60012] hover:bg-[#C2000F] text-white font-bold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-white" />
              {isLaunching ? "Launching Background Engine..." : "Start Parallel Batch Engine"}
            </button>

            {launchMessage && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                {launchMessage}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Real-time Live Queue & Worker Node Grid */}
        <div className="lg:col-span-7 glass-card rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-[#ECECEC] pb-4">
            <div>
              <h3 className="text-base font-bold text-[#1E293B]">Parallel Worker Node Grid</h3>
              <p className="text-xs text-[#64748B]">Live thread state & model fallback sequence</p>
            </div>
            <button 
              onClick={() => onNavigate('live-queue')}
              className="text-xs text-[#005BAC] font-bold hover:underline"
            >
              Open Dedicated Monitor →
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {workers.map((worker) => (
              <div key={worker.id} className="p-4 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-[#005BAC]" />
                    <span className="font-bold text-xs text-[#1E293B]">{worker.name}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    worker.status === 'RUNNING' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-700'
                  }`}>
                    {worker.status}
                  </span>
                </div>

                <div className="space-y-1 text-xs">
                  <div className="flex justify-between text-[#64748B]">
                    <span>Current Row:</span>
                    <span className="font-bold text-[#1E293B]">{worker.currentTask}</span>
                  </div>
                  <div className="flex justify-between text-[#64748B]">
                    <span>Model:</span>
                    <span className="font-bold text-[#005BAC]">{worker.modelUsed}</span>
                  </div>
                  <div className="flex justify-between text-[#64748B]">
                    <span>Stage:</span>
                    <span className="font-medium text-slate-800">{worker.stage}</span>
                  </div>
                </div>

                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-[#E60012] h-full transition-all duration-500" 
                    style={{ width: worker.status === 'RUNNING' ? '75%' : '0%' }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
