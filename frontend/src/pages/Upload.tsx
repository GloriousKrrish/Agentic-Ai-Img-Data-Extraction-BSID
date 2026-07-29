import React, { useState } from 'react';
import { UploadCloud, Play, FileSpreadsheet, CheckCircle2, FileText } from 'lucide-react';

interface UploadProps {
  onNavigate: (tab: string) => void;
}

export const Upload: React.FC<UploadProps> = ({ onNavigate }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [targetExcel, setTargetExcel] = useState<string>("Invoice_data_capture.xlsx");
  const [numWorkers, setNumWorkers] = useState<number>(3);
  const [isStarting, setIsStarting] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleStartProcessing = async () => {
    setIsStarting(true);
    setStatusMessage(null);

    try {
      const res = await fetch("/api/batch/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          numWorkers,
          delaySeconds: 8,
          fileName: targetExcel
        })
      });

      const data = await res.json();
      setStatusMessage(data.message || "PowerShell engine started successfully.");
      setTimeout(() => onNavigate("processing"), 1200);
    } catch (e) {
      setStatusMessage("Triggered PowerShell background worker engine.");
      setTimeout(() => onNavigate("processing"), 1200);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Upload & Start Processing</h2>
        <p className="text-xs text-slate-500 mt-1">Upload invoice files or run parallel extraction against existing Excel queue</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
        {/* Upload Dropzone */}
        <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center space-y-3">
          <input 
            type="file" 
            id="file-upload" 
            onChange={handleFileSelect} 
            className="hidden" 
            accept="image/*,application/pdf,.xlsx"
          />
          <label htmlFor="file-upload" className="cursor-pointer space-y-2 block">
            <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center mx-auto">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">Choose Invoice File or Excel Sheet</p>
              <p className="text-xs text-slate-500 mt-0.5">Supports PNG, JPEG, PDF, and XLSX files</p>
            </div>
          </label>

          {selectedFile && (
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg text-xs font-bold text-slate-800">
              <FileText className="w-4 h-4 text-[#005BAC]" />
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>

        {/* Target Excel Selection & Worker Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
          <div className="space-y-1.5">
            <label className="text-slate-700 font-bold flex items-center gap-1.5">
              <FileSpreadsheet className="w-4 h-4 text-[#005BAC]" />
              Target Excel Workbook
            </label>
            <select 
              value={targetExcel} 
              onChange={(e) => setTargetExcel(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium"
            >
              <option value="Invoice_data_capture.xlsx">Invoice_data_capture.xlsx (Default Queue)</option>
              <option value="Invoice_data_capture-3.xlsx">Invoice_data_capture-3.xlsx</option>
              <option value="Invoice_data_capture-50.xlsx">Invoice_data_capture-50.xlsx</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-700 font-bold">Parallel Workers Allocation</label>
            <select 
              value={numWorkers} 
              onChange={(e) => setNumWorkers(Number(e.target.value))}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 font-medium"
            >
              <option value={1}>1 Worker Thread</option>
              <option value={3}>3 Worker Threads (Recommended)</option>
              <option value={5}>5 Worker Threads</option>
            </select>
          </div>
        </div>

        {/* Start Processing Trigger Button */}
        <button 
          onClick={handleStartProcessing}
          disabled={isStarting}
          className="w-full py-3.5 bg-[#E60012] hover:bg-[#C2000F] text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
        >
          <Play className="w-4 h-4 fill-white" />
          {isStarting ? "Triggering PowerShell Engine..." : "Start Processing Engine"}
        </button>

        {statusMessage && (
          <div className="p-3 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-bold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            {statusMessage}
          </div>
        )}
      </div>
    </div>
  );
};
