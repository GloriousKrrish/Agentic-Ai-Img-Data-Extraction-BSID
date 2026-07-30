import React, { useState, useRef } from 'react';
import { 
  Play, 
  Cpu, 
  Clock, 
  CheckCircle2, 
  Sliders, 
  Sparkles,
  Upload,
  X,
  FileText,
  Image,
  FileSpreadsheet,
  Loader2,
  ExternalLink
} from 'lucide-react';
import { getApiUrl } from '../config/api';
import type { SystemKPIs, WorkerNode } from '../types';

interface BatchProcessingProps {
  kpis: SystemKPIs;
  workers: WorkerNode[];
  onNavigate: (tab: string) => void;
}

interface QueuedFile {
  file: File;
  jobId?: string;
  status: 'pending' | 'uploading' | 'queued' | 'error';
  error?: string;
}

const getFileIcon = (file: File) => {
  if (file.type.startsWith('image/')) return <Image className="w-4 h-4 text-purple-500" />;
  if (file.type.includes('pdf')) return <FileText className="w-4 h-4 text-red-500" />;
  if (file.type.includes('spreadsheet') || file.type.includes('excel') || file.name.endsWith('.xlsx') || file.name.endsWith('.csv'))
    return <FileSpreadsheet className="w-4 h-4 text-emerald-600" />;
  return <FileText className="w-4 h-4 text-slate-500" />;
};

const formatBytes = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const BatchProcessing: React.FC<BatchProcessingProps> = ({ kpis, workers, onNavigate }) => {
  const [queuedFiles, setQueuedFiles] = useState<QueuedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [delaySeconds, setDelaySeconds] = useState<number>(3);
  const [doneCount, setDoneCount] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = (files: FileList | File[]) => {
    const newFiles: QueuedFile[] = Array.from(files).map(f => ({
      file: f,
      status: 'pending'
    }));
    setQueuedFiles(prev => [...prev, ...newFiles]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) addFiles(e.dataTransfer.files);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(e.target.files);
  };

  const removeFile = (index: number) => {
    setQueuedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const runBatch = async () => {
    if (queuedFiles.length === 0 || isRunning) return;
    setIsRunning(true);
    setDoneCount(0);

    const pending = queuedFiles.filter(q => q.status === 'pending');

    for (let i = 0; i < pending.length; i++) {
      const qf = pending[i];
      const idx = queuedFiles.findIndex(q => q.file === qf.file);

      // Mark as uploading
      setQueuedFiles(prev => prev.map((q, j) => j === idx ? { ...q, status: 'uploading' } : q));

      try {
        const formData = new FormData();
        formData.append('file', qf.file);

        const res = await fetch(getApiUrl('/api/jobs'), {
          method: 'POST',
          body: formData,
        });

        if (res.ok) {
          const data = await res.json();
          setQueuedFiles(prev => prev.map((q, j) => j === idx ? {
            ...q,
            status: 'queued',
            jobId: data.jobId
          } : q));
          // Save latest job id
          localStorage.setItem('current_active_job_id', data.jobId);
        } else {
          const errJson = await res.json().catch(() => ({}));
          setQueuedFiles(prev => prev.map((q, j) => j === idx ? {
            ...q,
            status: 'error',
            error: errJson.detail || 'Upload failed'
          } : q));
        }
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        setQueuedFiles(prev => prev.map((q, j) => j === idx ? {
          ...q,
          status: 'error',
          error: msg
        } : q));
      }

      setDoneCount(i + 1);

      // Pacing delay between uploads to respect rate limits
      if (i < pending.length - 1 && delaySeconds > 0) {
        await new Promise(r => setTimeout(r, delaySeconds * 1000));
      }
    }

    setIsRunning(false);
  };

  const clearCompleted = () => {
    setQueuedFiles(prev => prev.filter(q => q.status === 'pending' || q.status === 'uploading'));
  };

  const pendingCount = queuedFiles.filter(q => q.status === 'pending').length;
  const queuedCount = queuedFiles.filter(q => q.status === 'queued').length;
  const errorCount = queuedFiles.filter(q => q.status === 'error').length;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-[#005BAC] to-slate-900 text-white rounded-2xl p-8 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-80 h-80 bg-[#E6001220] rounded-full blur-3xl -mr-16 -mt-16"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-xs font-bold mb-3 border border-white/20">
              <Sparkles className="w-3.5 h-3.5 text-[#E60012]" /> Batch AI Extraction Engine
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight">Bulk Document Batch Processing</h2>
            <p className="text-sm text-slate-200 mt-1 max-w-2xl">
              Queue multiple images, PDFs, and documents. Each file gets its own persistent backend job — auto-classified and extracted by Gemini Vision.
            </p>
          </div>

          <div className="flex gap-4">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/15 text-center min-w-[120px]">
              <span className="text-[10px] uppercase font-bold text-slate-300">In Queue</span>
              <div className="text-3xl font-extrabold text-white mt-0.5">{pendingCount}</div>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/15 text-center min-w-[120px]">
              <span className="text-[10px] uppercase font-bold text-slate-300">Submitted</span>
              <div className="text-3xl font-extrabold text-emerald-300 mt-0.5">{queuedCount}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Controls */}
        <div className="lg:col-span-4 space-y-6">
          {/* Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition-all space-y-3 ${
              isDragging
                ? 'border-[#E60012] bg-[#E6001208]'
                : 'border-slate-300 hover:border-[#E60012] bg-slate-50 hover:bg-[#E6001204]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleInputChange}
              className="hidden"
              accept="image/*,.pdf,.docx,.xlsx,.xls,.csv,.json,.xml,.txt,.zip"
            />
            <div className="w-12 h-12 rounded-xl bg-[#E600120F] text-[#E60012] flex items-center justify-center mx-auto">
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-extrabold text-slate-800">
                {isDragging ? 'Drop files here!' : 'Drop Files or Click to Browse'}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Select multiple images, PDFs, DOCX, XLSX, etc.
              </p>
            </div>
          </div>

          {/* Settings Card */}
          <div className="glass-card rounded-2xl p-5 space-y-5">
            <div className="border-b border-[#ECECEC] pb-3">
              <h3 className="text-sm font-bold text-[#1E293B] flex items-center gap-2">
                <Sliders className="w-4 h-4 text-[#005BAC]" />
                Batch Controls
              </h3>
            </div>

            {/* Delay Slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-[#1E293B]">Delay Between Uploads</label>
                <span className="text-xs font-extrabold text-[#005BAC] bg-[#005BAC10] px-2 py-0.5 rounded-full">
                  {delaySeconds}s
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="10"
                value={delaySeconds}
                onChange={(e) => setDelaySeconds(parseInt(e.target.value))}
                className="w-full accent-[#005BAC] cursor-pointer"
              />
              <p className="text-[10px] text-slate-500">
                Increase if you hit API quota limits. Recommended: 3–5s for free tier.
              </p>
            </div>

            {/* Run Button */}
            <button
              onClick={runBatch}
              disabled={pendingCount === 0 || isRunning}
              className="w-full py-3 bg-[#E60012] hover:bg-[#C2000F] text-white font-bold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing {doneCount}/{queuedFiles.filter(q=>q.status !== 'pending').length + pendingCount}...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  Start Batch — {pendingCount} File{pendingCount !== 1 ? 's' : ''}
                </>
              )}
            </button>

            {queuedCount > 0 && (
              <button
                onClick={() => onNavigate('results')}
                className="w-full py-2.5 bg-[#005BAC] hover:bg-[#004787] text-white font-bold text-xs rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <ExternalLink className="w-4 h-4" />
                View Results ({queuedCount} Jobs)
              </button>
            )}

            {(queuedCount > 0 || errorCount > 0) && (
              <button
                onClick={clearCompleted}
                className="w-full py-2 border border-slate-300 text-slate-600 text-xs font-bold rounded-xl hover:bg-slate-50 transition-all cursor-pointer"
              >
                Clear Submitted / Errors
              </button>
            )}
          </div>
        </div>

        {/* Right: File Queue & Worker Grid */}
        <div className="lg:col-span-8 space-y-6">
          {/* File Queue */}
          <div className="glass-card rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#ECECEC] pb-3">
              <h3 className="text-sm font-bold text-[#1E293B]">
                Upload Queue ({queuedFiles.length} files)
              </h3>
              {isRunning && (
                <span className="flex items-center gap-1.5 text-xs font-bold text-amber-600 bg-amber-50 px-3 py-1 rounded-full border border-amber-200 animate-pulse">
                  <Clock className="w-3.5 h-3.5" />
                  Batch Running...
                </span>
              )}
            </div>

            {queuedFiles.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-xs">
                <Upload className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                <p>No files queued. Drop files or click the upload area.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {queuedFiles.map((qf, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center gap-3 p-3 rounded-xl border text-xs transition-all ${
                      qf.status === 'queued'
                        ? 'bg-emerald-50 border-emerald-200'
                        : qf.status === 'uploading'
                        ? 'bg-blue-50 border-blue-200 animate-pulse'
                        : qf.status === 'error'
                        ? 'bg-red-50 border-red-200'
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    {getFileIcon(qf.file)}
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-slate-800 truncate">{qf.file.name}</p>
                      <p className="text-slate-500">{formatBytes(qf.file.size)}</p>
                      {qf.error && <p className="text-red-600 font-semibold truncate">{qf.error}</p>}
                      {qf.jobId && <p className="text-emerald-600 font-mono">{qf.jobId}</p>}
                    </div>
                    <div className="flex items-center gap-2">
                      {qf.status === 'queued' && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
                      {qf.status === 'uploading' && <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />}
                      {qf.status === 'pending' && !isRunning && (
                        <button
                          onClick={() => removeFile(idx)}
                          className="p-1 text-slate-400 hover:text-red-500 rounded"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Worker Node Grid */}
          <div className="glass-card rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#ECECEC] pb-3">
              <div>
                <h3 className="text-sm font-bold text-[#1E293B]">Active Backend Job Workers</h3>
                <p className="text-xs text-[#64748B]">Live job threads from the SQLite job manager</p>
              </div>
              <span className="text-xs font-bold text-slate-500">
                {kpis.processedDocuments} processed / {kpis.totalDocuments} total
              </span>
            </div>

            {workers.length > 0 ? (
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
                        <span>Task:</span>
                        <span className="font-bold text-[#1E293B] truncate max-w-[150px]">{worker.currentTask || '—'}</span>
                      </div>
                      <div className="flex justify-between text-[#64748B]">
                        <span>Model:</span>
                        <span className="font-bold text-[#005BAC]">{worker.modelUsed || '—'}</span>
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
            ) : (
              <div className="py-8 text-center text-slate-400 text-xs">
                No active workers. Upload files and run batch to start.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
