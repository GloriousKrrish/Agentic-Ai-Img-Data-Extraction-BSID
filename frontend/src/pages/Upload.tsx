import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, Sparkles, FileText, CheckCircle2, Loader2, Image, FileSpreadsheet, FileCode, Archive, AlertCircle, ArrowRight, Bot, Brain, ChevronDown } from 'lucide-react';
import { getApiUrl } from '../config/api';

interface UploadProps {
  onNavigate: (tab: string) => void;
  onJobCreated?: (jobId: string) => void;
}

type UploadState = 'idle' | 'uploading' | 'queued' | 'error';

export const Upload: React.FC<UploadProps> = ({ onNavigate, onJobCreated }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Phase 4: Schema picker
  const [useCustomSchema, setUseCustomSchema] = useState(false);
  const [savedSchemas, setSavedSchemas] = useState<any[]>([]);
  const [selectedSchemaId, setSelectedSchemaId] = useState('');

  const isImage = (file: File) => file.type.startsWith('image/');

  // Phase 4: Load saved schemas for picker
  useEffect(() => {
    fetch(getApiUrl('/api/schemas'))
      .then(r => r.ok ? r.json() : [])
      .then(d => setSavedSchemas(d))
      .catch(() => {});
  }, []);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadState('idle');
    setStatusMessage(null);
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

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      // Phase 4: attach schema_id if user selected a custom schema
      if (useCustomSchema && selectedSchemaId) {
        formData.append('schema_id', selectedSchemaId);
      }
      const res = await fetch(getApiUrl('/api/jobs'), { method: 'POST', body: formData, signal: controller.signal });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        const jobId = data.jobId || data.job_id || 'JOB-ACTIVE';
        localStorage.setItem('current_active_job_id', jobId);
        if (onJobCreated) onJobCreated(jobId);
        setUploadState('queued');
        setStatusMessage(`Job ${jobId} created successfully! Extraction in progress.`);
      } else {
        const errJson = await res.json().catch(() => ({}));
        const errMsg = errJson.detail || 'Upload failed';
        if (errMsg.toLowerCase().includes('quota') || errMsg.toLowerCase().includes('429')) {
          setStatusMessage(`API Quota Exceeded. Go to Settings to update your API key.`);
        } else {
          setStatusMessage(`Error: ${errMsg}`);
        }
        setUploadState('error');
      }
    } catch (e: unknown) {
      clearTimeout(timeoutId);
      setUploadState('error');
      if (e instanceof Error && e.name === 'AbortError') {
        setStatusMessage('Upload timed out. Please try again.');
      } else {
        setStatusMessage(`Network error: ${e instanceof Error ? e.message : String(e)}`);
      }
    }
  };

  const formatBytes = (b: number) => b < 1024 ? `${b} B` : b < 1048576 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1048576).toFixed(1)} MB`;

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <Image size={20} color="#4F46E5" />;
    if (file.type.includes('pdf')) return <FileText size={20} color="#DC2626" />;
    if (file.type.includes('spreadsheet') || file.type.includes('excel') || file.name.endsWith('.xlsx') || file.name.endsWith('.csv'))
      return <FileSpreadsheet size={20} color="#059669" />;
    if (file.name.endsWith('.json') || file.name.endsWith('.xml') || file.name.endsWith('.docx'))
      return <FileCode size={20} color="#2563EB" />;
    if (file.name.endsWith('.zip')) return <Archive size={20} color="#D97706" />;
    return <FileText size={20} color="#64748B" />;
  };

  return (
    <div style={{ padding: '2.5rem 2rem', maxWidth: 840, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
        <div className="badge badge-indigo">
          <Bot size={14} style={{ marginRight: 4 }} />
          Multimodal AI Intelligence Engine
        </div>
        <h1 style={{ fontSize: 30, fontWeight: 800, color: '#0F172A', margin: 0, letterSpacing: '-0.025em' }}>
          Upload Any Document
        </h1>
        <p style={{ fontSize: 14, color: '#64748B', margin: 0, maxWidth: 540, lineHeight: 1.5 }}>
          Drop invoices, receipts, medical bills, PDFs, images, Excel sheets or ZIP archives for automatic multimodal field extraction.
        </p>
      </div>

      {/* Main Upload Card */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '2rem' }}>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleInputChange}
            accept="image/*,.pdf,.xlsx,.csv,.docx,.json,.xml,.zip"
            style={{ display: 'none' }}
          />

          <div
            className={`drop-zone ${isDragging ? 'dragging' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
              minHeight: 240,
              justifyContent: 'center',
            }}
          >
            {previewUrl ? (
              <div style={{ position: 'relative', maxWidth: 200, maxHeight: 150, borderRadius: 8, overflow: 'hidden', border: '1px solid #CBD5E1' }}>
                <img src={previewUrl} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
            ) : (
              <div style={{
                width: 56, 
                height: 56, 
                borderRadius: 12,
                background: '#EEF2FF',
                border: '1px solid #C7D2FE',
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
              }}>
                <UploadCloud size={28} color="#4F46E5" />
              </div>
            )}

            {selectedFile ? (
              <div>
                <div style={{ 
                  display: 'inline-flex', 
                  alignItems: 'center', 
                  gap: 10, 
                  padding: '8px 16px', 
                  background: '#FFFFFF', 
                  borderRadius: 8, 
                  border: '1px solid #E2E8F0',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                }}>
                  {getFileIcon(selectedFile)}
                  <span style={{ fontSize: 14, fontWeight: 700, color: '#0F172A' }}>{selectedFile.name}</span>
                  <span style={{ fontSize: 12, color: '#64748B', fontWeight: 500 }}>({formatBytes(selectedFile.size)})</span>
                </div>
                <p style={{ fontSize: 12, color: '#64748B', margin: '8px 0 0', fontWeight: 500 }}>
                  Click or drag another file to replace
                </p>
              </div>
            ) : (
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0F172A', margin: 0 }}>
                  Drag &amp; drop files here, or <span style={{ color: '#4F46E5', cursor: 'pointer' }}>browse</span>
                </h3>
                <p style={{ fontSize: 12, color: '#64748B', margin: '6px 0 0', fontWeight: 500 }}>
                  Supports PNG, JPG, PDF, XLSX, CSV, DOCX, JSON, ZIP up to 50MB
                </p>
              </div>
            )}
          </div>

          {/* Phase 4: Custom Schema Picker */}
          <div style={{ marginTop: '1.25rem', padding: '0.85rem 1.1rem', background: '#F8FAFF', border: '1px solid #E0E7FF', borderRadius: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Brain size={15} color="#4F46E5" />
                <span style={{ fontWeight: 700, fontSize: 13, color: '#3730A3' }}>Use Custom Schema</span>
                <span style={{ fontSize: 11, color: '#64748B' }}>Extract only your defined fields</span>
              </div>
              <div onClick={() => setUseCustomSchema(v => !v)} style={{
                width: 38, height: 22, borderRadius: 999, cursor: 'pointer', transition: 'all 0.2s',
                background: useCustomSchema ? '#4F46E5' : '#CBD5E1', position: 'relative'
              }}>
                <div style={{
                  width: 16, height: 16, borderRadius: '50%', background: 'white',
                  position: 'absolute', top: 3, left: useCustomSchema ? 19 : 3, transition: 'all 0.2s',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
                }} />
              </div>
            </div>
            {useCustomSchema && (
              <div style={{ marginTop: 10 }}>
                {savedSchemas.length > 0 ? (
                  <select value={selectedSchemaId} onChange={e => setSelectedSchemaId(e.target.value)}
                    style={{
                      width: '100%', borderRadius: 8, border: '1px solid #C7D2FE', padding: '0.5rem 0.75rem',
                      fontSize: 13, background: 'white', color: '#0F172A', outline: 'none'
                    }}>
                    <option value="">-- Select a saved schema --</option>
                    {savedSchemas.map((s: any) => (
                      <option key={s.schema_id} value={s.schema_id}>
                        {s.name} (v{s.version}) · {s.domain}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div style={{ fontSize: 12, color: '#94A3B8', padding: '0.5rem', textAlign: 'center' }}>
                    No saved schemas found. Go to the <strong>Schema Builder</strong> to create one.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Bar */}
          <div style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
            <button
              onClick={handleExtract}
              disabled={!selectedFile || uploadState === 'uploading'}
              className="btn-primary"
              style={{
                opacity: !selectedFile || uploadState === 'uploading' ? 0.5 : 1,
                cursor: !selectedFile || uploadState === 'uploading' ? 'not-allowed' : 'pointer',
              }}
            >
              {uploadState === 'uploading' ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Uploading &amp; Processing...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>{useCustomSchema && selectedSchemaId ? 'Extract with Custom Schema' : 'Start Agentic AI Extraction'}</span>
                </>
              )}
            </button>
          </div>

          {/* Status Alert Banner */}
          {statusMessage && (
            <div style={{
              marginTop: '1.25rem',
              padding: '1rem 1.25rem',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              background: uploadState === 'queued' ? '#ECFDF5' : uploadState === 'error' ? '#FEF2F2' : '#EEF2FF',
              border: `1px solid ${uploadState === 'queued' ? '#A7F3D0' : uploadState === 'error' ? '#FECACA' : '#C7D2FE'}`,
              color: uploadState === 'queued' ? '#047857' : uploadState === 'error' ? '#B91C1C' : '#4338CA',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {uploadState === 'queued' && <CheckCircle2 size={18} color="#047857" />}
                {uploadState === 'error' && <AlertCircle size={18} color="#B91C1C" />}
                {uploadState === 'uploading' && <Loader2 size={18} className="animate-spin" color="#4338CA" />}
                <span style={{ fontSize: 13, fontWeight: 600 }}>{statusMessage}</span>
              </div>

              {uploadState === 'queued' && (
                <button
                  onClick={() => onNavigate('results')}
                  style={{
                    background: '#FFFFFF',
                    border: '1px solid #A7F3D0',
                    color: '#047857',
                    padding: '6px 12px',
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span>View Results</span> <ArrowRight size={12} />
                </button>
              )}
            </div>
          )}
        </div>

        {/* Card Footer Bar */}
        <div style={{
          background: '#F8FAFC',
          borderTop: '1px solid #E2E8F0',
          padding: '0.85rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: 12,
          color: '#64748B',
          fontWeight: 500,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Sparkles size={14} color="#4F46E5" />
            <span>OpenCV Auto-Deskew &amp; CLAHE Image Preprocessing Active</span>
          </div>
          <span>API Model: Gemini 2.5 Flash</span>
        </div>
      </div>
    </div>
  );
};
