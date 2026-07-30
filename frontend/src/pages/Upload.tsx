import React, { useState } from 'react';
import { UploadCloud, Sparkles, FileText, CheckCircle2, Loader2, FileSpreadsheet, FileCode, Archive } from 'lucide-react';
import type { SchemaColumn, DynamicRow } from '../types';

interface UploadProps {
  onNavigate: (tab: string) => void;
  onDatasetExtracted?: (dataset: { schema: SchemaColumn[]; rows: DynamicRow[] }) => void;
}

export const Upload: React.FC<UploadProps> = ({ onNavigate }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleUniversalExtract = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setStatusMessage(`Creating persistent backend job for ${selectedFile.name}...`);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetch("/api/jobs", {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        const jobId = data.jobId;
        localStorage.setItem("current_active_job_id", jobId);
        setStatusMessage(`Job ${jobId} created! Background AI extraction running...`);
        setTimeout(() => onNavigate("results"), 600);
      } else {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to create backend job");
      }
    } catch (e: any) {
      setStatusMessage(`Error: ${e.message || 'Failed to create job'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-5xl mx-auto">
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#E6001210] text-[#E60012] rounded-full text-xs font-bold border border-[#E6001220]">
          <Sparkles className="w-3.5 h-3.5" />
          Enterprise Persistent Job Manager & Universal AI Platform
        </div>
        <h1 className="text-3xl font-black text-[#1E293B] tracking-tight">Drop Anything Here</h1>
        <p className="text-xs text-slate-500 max-w-xl mx-auto">
          Upload ANY PDF, scanned document, image, Word document, Excel spreadsheet, CSV, JSON, XML, TXT, or ZIP archive. Jobs run asynchronously on backend threads.
        </p>
      </div>

      <div className="glass-card rounded-3xl p-8 space-y-6 shadow-xl border border-slate-200">
        {/* Universal Dropzone */}
        <div 
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className="border-2 border-dashed border-slate-300 hover:border-[#E60012] transition-all rounded-2xl p-12 text-center cursor-pointer space-y-4 bg-slate-50/50"
        >
          <input 
            type="file" 
            id="universal-file-upload" 
            onChange={handleFileSelect} 
            className="hidden" 
          />
          <label htmlFor="universal-file-upload" className="cursor-pointer space-y-3 block">
            <div className="w-16 h-16 rounded-2xl bg-[#E600120F] text-[#E60012] flex items-center justify-center mx-auto shadow-sm">
              <UploadCloud className="w-8 h-8" />
            </div>
            <div>
              <p className="text-base font-extrabold text-[#1E293B]">Drag & Drop Any File or Click to Browse</p>
              <p className="text-xs text-slate-500 mt-1">Supports PDF, PNG, JPG, DOCX, XLSX, CSV, JSON, XML, TXT, ZIP up to 50MB</p>
            </div>
          </label>

          {selectedFile && (
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-xl text-xs font-bold text-slate-800 border border-slate-200 shadow-sm">
              <FileText className="w-4 h-4 text-[#005BAC]" />
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>

        {/* Format Badges Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-semibold text-slate-600 pt-2">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#E60012]" />
            PDF & Scanned Papers
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            Excel, CSV & Workbooks
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-2">
            <FileCode className="w-4 h-4 text-[#005BAC]" />
            Word, JSON & XML
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-2">
            <Archive className="w-4 h-4 text-amber-600" />
            ZIP Archives & Batches
          </div>
        </div>

        {/* Action Button */}
        <button 
          onClick={handleUniversalExtract}
          disabled={!selectedFile || isProcessing}
          className="w-full py-4 bg-[#E60012] hover:bg-[#C2000F] text-white font-extrabold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Enqueueing Persistent Job...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Enqueue Persistent Processing Job
            </>
          )}
        </button>

        {statusMessage && (
          <div className="p-4 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-bold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            {statusMessage}
          </div>
        )}
      </div>
    </div>
  );
};
