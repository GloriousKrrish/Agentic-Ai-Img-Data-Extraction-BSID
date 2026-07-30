import React, { useState, useRef } from 'react';
import { UploadCloud, Sparkles, FileText, CheckCircle2, Loader2, Image, FileSpreadsheet, FileCode, Archive, AlertCircle, ExternalLink } from 'lucide-react';
import { getApiUrl } from '../config/api';

interface UploadProps {
  onNavigate: (tab: string) => void;
}

type UploadState = 'idle' | 'uploading' | 'queued' | 'error';

export const Upload: React.FC<UploadProps> = ({ onNavigate }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [createdJobId, setCreatedJobId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isImage = (file: File) => file.type.startsWith('image/');

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadState('idle');
    setStatusMessage(null);
    setCreatedJobId(null);
    if (isImage(file)) {
      setPreviewUrl(URL.createObjectURL(file));
    } else {
      setPreviewUrl(null);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) handleFileSelect(e.target.files[0]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleExtract = async () => {
    if (!selectedFile) return;
    setUploadState('uploading');
    setStatusMessage(`Uploading ${selectedFile.name}...`);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const res = await fetch(getApiUrl('/api/jobs'), {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        const jobId = data.jobId;
        setCreatedJobId(jobId);
        localStorage.setItem('current_active_job_id', jobId);
        setUploadState('queued');
        setStatusMessage(`Job ${jobId} created! AI is extracting data in the background.`);
      } else {
        const errJson = await res.json().catch(() => ({}));
        const errMsg = errJson.detail || 'Upload failed';
        // Check for quota error hint
        if (errMsg.toLowerCase().includes('quota') || errMsg.toLowerCase().includes('429')) {
          setStatusMessage(`API Quota Exceeded. Go to Settings → paste a new Gemini API key.`);
        } else {
          setStatusMessage(`Error: ${errMsg}`);
        }
        setUploadState('error');
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setUploadState('error');
      setStatusMessage(`Network error: ${msg}`);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <Image className="w-4 h-4 text-purple-500" />;
    if (file.type.includes('pdf')) return <FileText className="w-4 h-4 text-red-500" />;
    if (file.type.includes('spreadsheet') || file.type.includes('excel') || file.name.endsWith('.xlsx') || file.name.endsWith('.csv'))
      return <FileSpreadsheet className="w-4 h-4 text-emerald-600" />;
    if (file.name.endsWith('.json') || file.name.endsWith('.xml') || file.name.endsWith('.docx'))
      return <FileCode className="w-4 h-4 text-blue-500" />;
    if (file.name.endsWith('.zip')) return <Archive className="w-4 h-4 text-amber-600" />;
    return <FileText className="w-4 h-4 text-slate-500" />;
  };

  return (
    <div className="p-8 space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#E6001210] text-[#E60012] rounded-full text-xs font-bold border border-[#E6001220]">
          <Sparkles className="w-3.5 h-3.5" />
          Universal AI Document Intelligence — Image, PDF, Excel, Word &amp; More
        </div>
        <h1 className="text-3xl font-black text-[#1E293B] tracking-tight">Upload Any Document</h1>
        <p className="text-xs text-slate-500 max-w-xl mx-auto">
          Drop an image, PDF, scanned document, or any file. Gemini Vision will automatically detect what it is and extract every field — no templates, no configuration.
        </p>
      </div>

      <div className="glass-card rounded-3xl p-8 space-y-6 shadow-xl border border-slate-200">
        {/* Dropzone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer space-y-4 transition-all ${
            isDragging
              ? 'border-[#E60012] bg-[#E6001208] scale-[1.01]'
              : 'border-slate-300 hover:border-[#E60012] bg-slate-50/50 hover:bg-[#E6001204]'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            id="universal-file-upload"
            onChange={handleInputChange}
            className="hidden"
            accept="image/*,.pdf,.docx,.xlsx,.xls,.csv,.json,.xml,.txt,.zip"
          />

          {/* Image Preview */}
          {previewUrl && selectedFile && isImage(selectedFile) ? (
            <div className="space-y-3">
              <div className="relative inline-block">
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="max-h-48 max-w-full mx-auto rounded-xl shadow-md object-contain border border-slate-200"
                />
                <span className="absolute -top-2 -right-2 bg-emerald-500 text-white text-[10px] font-black px-2 py-0.5 rounded-full">
                  IMAGE
                </span>
              </div>
              <p className="text-xs text-slate-500">Click or drag to change file</p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="w-16 h-16 rounded-2xl bg-[#E600120F] text-[#E60012] flex items-center justify-center mx-auto shadow-sm">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div>
                <p className="text-base font-extrabold text-[#1E293B]">
                  {isDragging ? 'Drop it here!' : 'Drag & Drop Any File or Click to Browse'}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Images (JPG, PNG, WEBP) · PDF · DOCX · XLSX · CSV · JSON · XML · ZIP · up to 50MB
                </p>
              </div>
            </div>
          )}

          {/* Selected File Info (non-image) */}
          {selectedFile && !isImage(selectedFile) && (
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-xl text-xs font-bold text-slate-800 border border-slate-200 shadow-sm">
              {getFileIcon(selectedFile)}
              {selectedFile.name} ({formatBytes(selectedFile.size)})
            </div>
          )}

          {/* Image file info below preview */}
          {selectedFile && isImage(selectedFile) && (
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white rounded-xl text-xs font-bold text-slate-800 border border-slate-200 shadow-sm">
              {getFileIcon(selectedFile)}
              {selectedFile.name} — {formatBytes(selectedFile.size)}
            </div>
          )}
        </div>

        {/* Format Badges */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-semibold text-slate-600">
          <div className="p-3 rounded-xl bg-purple-50 border border-purple-200 flex items-center gap-2">
            <Image className="w-4 h-4 text-purple-500" />
            JPG · PNG · WEBP
          </div>
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 flex items-center gap-2">
            <FileText className="w-4 h-4 text-red-500" />
            PDF · Scanned Docs
          </div>
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            Excel · CSV
          </div>
          <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 flex items-center gap-2">
            <FileCode className="w-4 h-4 text-blue-500" />
            DOCX · JSON · XML
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={handleExtract}
          disabled={!selectedFile || uploadState === 'uploading' || uploadState === 'queued'}
          className="w-full py-4 bg-[#E60012] hover:bg-[#C2000F] text-white font-extrabold text-sm rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploadState === 'uploading' ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Uploading &amp; Creating Job...
            </>
          ) : uploadState === 'queued' ? (
            <>
              <CheckCircle2 className="w-4 h-4" />
              Job Queued — Processing in Background
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Extract with AI — Auto-Detect &amp; Analyse
            </>
          )}
        </button>

        {/* Status Message */}
        {statusMessage && (
          <div className={`p-4 rounded-xl text-xs font-bold flex items-start gap-3 border ${
            uploadState === 'error'
              ? 'bg-red-50 text-red-800 border-red-200'
              : uploadState === 'queued'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : 'bg-blue-50 text-blue-800 border-blue-200'
          }`}>
            {uploadState === 'error' ? (
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            ) : (
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              {statusMessage}
              {uploadState === 'error' && statusMessage.includes('Quota') && (
                <div className="mt-2">
                  <a
                    href="https://aistudio.google.com/apikey"
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="inline-flex items-center gap-1 underline text-[#005BAC] font-bold"
                  >
                    Get a new API key at aistudio.google.com
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>
          </div>
        )}

        {/* View Results Button */}
        {uploadState === 'queued' && createdJobId && (
          <button
            onClick={() => onNavigate('results')}
            className="w-full py-3 bg-[#005BAC] hover:bg-[#004787] text-white font-bold text-xs rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <ExternalLink className="w-4 h-4" />
            View Live Results for Job {createdJobId}
          </button>
        )}
      </div>

      {/* How It Works */}
      <div className="glass-card rounded-2xl p-6">
        <h3 className="font-extrabold text-[#1E293B] text-sm mb-4">How It Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs text-slate-600">
          {[
            { step: '1', title: 'Upload Anything', desc: 'Drop any image, PDF, or document' },
            { step: '2', title: 'AI Classifies', desc: 'Gemini Vision reads and understands the document type' },
            { step: '3', title: 'Schema Generated', desc: 'Dynamic fields inferred — no templates needed' },
            { step: '4', title: 'Data Extracted', desc: 'Every field extracted and shown in the Results tab' },
          ].map(item => (
            <div key={item.step} className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-[#E60012] text-white text-xs font-black flex items-center justify-center shrink-0">
                {item.step}
              </div>
              <div>
                <p className="font-bold text-slate-800">{item.title}</p>
                <p className="text-slate-500 mt-0.5">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
