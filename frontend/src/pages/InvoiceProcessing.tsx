import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  Sparkles, 
  Download, 
  RotateCw, 
  ZoomIn, 
  ZoomOut, 
  ShieldCheck, 
  Loader2,
  RefreshCw,
  Tag,
  FileSpreadsheet
} from 'lucide-react';
import type { UniversalDataset } from '../types';

export const InvoiceProcessing: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [extractedDoc, setExtractedDoc] = useState<UniversalDataset | any | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [rotation, setRotation] = useState<number>(0);
  const [activeStage, setActiveStage] = useState<number>(0);
  const [activeModel, setActiveModel] = useState<string>("gemini-3.5-flash");

  useEffect(() => {
    fetch("/api/settings")
      .then(res => res.json())
      .then(data => {
        if (data.primaryModel) setActiveModel(data.primaryModel);
      })
      .catch(() => {});

    // Read latest document processed from localStorage if available
    const saved = localStorage.getItem("latest_universal_doc");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setExtractedDoc(parsed);
        setActiveStage(7);
      } catch (e) {}
    }
  }, []);

  const stages = [
    { title: "File Ingested", desc: "Multi-format detection" },
    { title: "Format Classification", desc: "Auto-detecting purpose" },
    { title: "Preprocessing & Enhance", desc: "Deskew, sharpen & rotate" },
    { title: "OCR / Vision Stage", desc: "Multimodal perception" },
    { title: `${activeModel} LLM Intelligence`, desc: "Contextual understanding" },
    { title: "Dynamic Schema Generator", desc: "Inferring bespoke fields" },
    { title: "Validation Engine", desc: "Field sanitization & checks" },
    { title: "Live Inspector Ready", desc: "Ready for dynamic export" }
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setExtractedDoc(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setExtractedDoc(null);
    }
  };

  const handleProcessDocument = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setActiveStage(1);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      setTimeout(() => setActiveStage(2), 400);
      setTimeout(() => setActiveStage(3), 800);
      setTimeout(() => setActiveStage(4), 1200);
      setTimeout(() => setActiveStage(5), 1600);
      setTimeout(() => setActiveStage(6), 2000);

      const res = await fetch("/api/extract/universal", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Failed to process document");
      }

      const data = await res.json();
      setActiveStage(7);
      setExtractedDoc(data);
      localStorage.setItem("latest_universal_doc", JSON.stringify(data));
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  const exportExcel = async () => {
    if (!extractedDoc) return;
    try {
      const res = await fetch("/api/export/dynamic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: [extractedDoc], format: "excel" })
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `dynamic_extracted_${Date.now()}.xlsx`;
      a.click();
    } catch (e) {}
  };

  const downloadJSON = () => {
    if (!extractedDoc) return;
    const blob = new Blob([JSON.stringify(extractedDoc, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `extracted_doc_${Date.now()}.json`;
    a.click();
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-[#1B1B1B] tracking-tight">Universal AI Document Inspector</h2>
          <p className="text-xs text-[#6B7280]">Dynamic multi-format document previewer & AI schema visualizer</p>
        </div>
        <div className="flex items-center gap-2">
          {extractedDoc?.category && (
            <span className="text-xs font-bold text-[#E60012] bg-[#E6001210] px-3 py-1.5 rounded-full border border-[#E6001220] flex items-center gap-1.5">
              <Tag className="w-3.5 h-3.5" />
              Category: {extractedDoc.category}
            </span>
          )}
          <span className="text-xs font-semibold text-[#005BAC] bg-[#005BAC10] px-3 py-1.5 rounded-full border border-[#005BAC20]">
            {activeModel} Model Active
          </span>
        </div>
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: File Upload & Interactive Image/PDF Previewer */}
        <div className="lg:col-span-6 space-y-6">
          {!previewUrl ? (
            <div 
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="glass-card rounded-2xl p-10 text-center border-2 border-dashed border-[#CBD5E1] hover:border-[#E60012] transition-colors cursor-pointer space-y-4"
            >
              <input 
                type="file" 
                onChange={handleFileChange} 
                className="hidden" 
                id="doc-upload-input"
              />
              <label htmlFor="doc-upload-input" className="cursor-pointer space-y-3 block">
                <div className="w-16 h-16 rounded-2xl bg-[#E600120D] text-[#E60012] flex items-center justify-center mx-auto shadow-xs">
                  <UploadCloud className="w-8 h-8" />
                </div>
                <div>
                  <p className="text-sm font-bold text-[#1E293B]">Select Any Document, Image, or File</p>
                  <p className="text-xs text-[#64748B] mt-1">PDF, Image, Word, Excel, CSV, JSON, XML, TXT</p>
                </div>
                <button type="button" className="px-4 py-2 bg-[#E60012] text-white text-xs font-semibold rounded-xl shadow-md">
                  Browse File
                </button>
              </label>
            </div>
          ) : (
            <div className="glass-card rounded-2xl p-4 space-y-4">
              <div className="flex items-center justify-between border-b border-[#ECECEC] pb-3">
                <span className="text-xs font-bold text-[#1E293B] truncate max-w-xs">{selectedFile?.name}</span>
                <div className="flex items-center gap-1.5">
                  <button 
                    onClick={() => setZoomLevel(prev => Math.min(prev + 0.2, 2.5))}
                    className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-600"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setZoomLevel(prev => Math.max(prev - 0.2, 0.6))}
                    className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-600"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setRotation(prev => (prev + 90) % 360)}
                    className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-600"
                    title="Rotate"
                  >
                    <RotateCw className="w-4 h-4" />
                  </button>
                  <label htmlFor="doc-upload-input" className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-600 cursor-pointer">
                    <RefreshCw className="w-4 h-4" />
                  </label>
                </div>
              </div>

              {/* Document Preview Canvas */}
              <div className="h-[480px] bg-slate-900 rounded-xl overflow-hidden flex items-center justify-center relative p-4">
                {selectedFile?.type.includes('pdf') ? (
                  <iframe src={previewUrl} className="w-full h-full rounded-lg" title="Document Preview" />
                ) : (
                  <motion.img 
                    src={previewUrl} 
                    alt="Document" 
                    style={{ transform: `scale(${zoomLevel}) rotate(${rotation}deg)` }}
                    transition={{ type: "spring", stiffness: 200, damping: 20 }}
                    className="max-h-full max-w-full object-contain rounded shadow-lg"
                  />
                )}
              </div>

              <button 
                onClick={handleProcessDocument}
                disabled={isProcessing}
                className="w-full py-3 bg-[#E60012] hover:bg-[#C2000F] text-white font-bold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Executing Universal AI Pipeline...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Infer Dynamic Schema & Extract
                  </>
                )}
              </button>
            </div>
          )}

          {/* 8-Stage Timeline */}
          <div className="glass-card rounded-2xl p-6 space-y-4">
            <h4 className="text-xs font-bold text-[#1E293B] uppercase tracking-wider">Live Universal Pipeline (8 Stages)</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {stages.map((stage, idx) => (
                <div key={idx} className="flex items-center gap-2.5 p-2 rounded-xl bg-slate-50 border border-slate-200">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    activeStage > idx 
                      ? 'bg-emerald-500 text-white' 
                      : activeStage === idx 
                      ? 'bg-[#E60012] text-white animate-pulse' 
                      : 'bg-slate-200 text-slate-500'
                  }`}>
                    {activeStage > idx ? <CheckCircle2 className="w-3.5 h-3.5" /> : idx + 1}
                  </div>
                  <div>
                    <p className={`text-xs font-bold ${activeStage >= idx ? 'text-[#1E293B]' : 'text-slate-400'}`}>{stage.title}</p>
                    <p className="text-[10px] text-slate-500">{stage.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Dynamic Extracted Fields Grid */}
        <div className="lg:col-span-6">
          <div className="glass-card rounded-2xl p-6 space-y-6 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-[#ECECEC] pb-4">
                <div>
                  <h3 className="text-base font-bold text-[#1E293B]">Auto-Discovered Dynamic Schema</h3>
                  <p className="text-xs text-[#64748B]">Zero hardcoded fields — dynamically inferred by AI</p>
                </div>
                {extractedDoc && (
                  <span className="px-3 py-1 bg-emerald-50 text-emerald-700 font-bold text-xs rounded-full border border-emerald-200 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    {extractedDoc.confidence}% Confidence
                  </span>
                )}
              </div>

              {extractedDoc ? (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mt-6 space-y-4"
                >
                  <div className="grid grid-cols-2 gap-3">
                    {(extractedDoc.rows && extractedDoc.rows[0] && extractedDoc.rows[0].fields 
                      ? Object.entries(extractedDoc.rows[0].fields)
                      : Object.entries(extractedDoc.extractedFields || {})
                    ).map(([key, value]) => {
                      const labelObj = extractedDoc.schema?.find((s: any) => s.key === key);
                      const displayLabel = labelObj ? labelObj.label : key.replace(/([A-Z])/g, ' $1').trim();
                      return (
                        <div key={key} className="p-3 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0]">
                          <span className="text-[10px] uppercase font-bold text-[#64748B] block truncate">
                            {displayLabel}
                          </span>
                          <p className="text-xs font-bold text-[#1E293B] mt-1 break-words">
                            {String(value || 'N/A')}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              ) : (
                <div className="py-20 text-center text-[#94A3B8] space-y-3">
                  <FileText className="w-12 h-12 mx-auto text-slate-300" />
                  <p className="text-xs font-medium">Upload any document to inspect auto-discovered AI schema fields.</p>
                </div>
              )}
            </div>

            {extractedDoc && (
              <div className="pt-4 border-t border-[#ECECEC] flex items-center justify-between gap-3">
                <button 
                  onClick={exportExcel}
                  className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  Export Dynamic Excel (.xlsx)
                </button>
                <button 
                  onClick={downloadJSON}
                  className="py-2.5 px-4 bg-slate-900 hover:bg-black text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Download className="w-4 h-4" />
                  JSON
                </button>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
