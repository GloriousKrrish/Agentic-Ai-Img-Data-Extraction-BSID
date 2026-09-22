import React from 'react';
import type { WorkerNode, LogEntry } from '../types';
import { Terminal, Clock, Activity, ArrowRight, FileText, Sparkles, Cpu } from 'lucide-react';

interface ProcessingProps {
  workers?: WorkerNode[];
  pendingTasks: number;
  activeLocks?: number;
  logs: LogEntry[];
  activeJob?: any | null;
  onNavigate?: (tab: string) => void;
}

const defaultAgentNodes: WorkerNode[] = [
  { id: 1, name: 'Vision AI Extractor', status: 'RUNNING', currentTask: 'Multimodal VLM extraction', stage: 'Gemini 2.5 Flash', modelUsed: 'gemini-2.5-flash', elapsed: '1.2s', confidence: 98.5, lastLog: 'Pyramid crop slicing on high-res input' },
  { id: 2, name: 'OCR & Preprocessor', status: 'RUNNING', currentTask: 'CLAHE contrast + deskew', stage: 'OpenCV', modelUsed: 'opencv-python', elapsed: '0.4s', confidence: 96.0, lastLog: 'Deskewed 0.5°, 300 DPI upscale done' },
  { id: 3, name: 'Math Auditor', status: 'READY', currentTask: 'Cross-field arithmetic audit', stage: 'Validation', modelUsed: 'sanitizer', elapsed: '0.1s', confidence: 100.0, lastLog: 'Verified: subtotal + tax == grand total' },
];

export const Processing: React.FC<ProcessingProps> = ({ workers = [], pendingTasks, logs, activeJob, onNavigate }) => {
  const isCompleted = activeJob?.status === 'Completed';
  const isFailed = activeJob?.status === 'Failed';
  const isProcessing = activeJob && !isCompleted && !isFailed;
  const progress = activeJob?.progress || (isCompleted ? 100 : 0);
  const displayWorkers = workers.length > 0 ? workers : defaultAgentNodes;

  return (
    <div style={{ padding: '2rem', maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: '#0F172A', margin: 0, letterSpacing: '-0.02em' }}>
            Job Queue &amp; AI Telemetry
          </h2>
          <p style={{ fontSize: 13, color: '#64748B', margin: '4px 0 0', fontWeight: 500 }}>
            Real-time multi-agent execution pipeline &amp; worker monitoring
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="badge badge-indigo" style={{ padding: '6px 12px' }}>
            <Clock size={14} style={{ marginRight: 6 }} /> {pendingTasks} Tasks Pending
          </div>
          <div className={isProcessing ? 'badge badge-success' : 'badge badge-neutral'} style={{ padding: '6px 12px' }}>
            <Activity size={14} style={{ marginRight: 6 }} /> {isProcessing ? 'Engine Active' : 'Engine Idle'}
          </div>
        </div>
      </div>

      {/* Active Job Progress Card */}
      {activeJob ? (
        <div className="card" style={{ padding: '1.75rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 16, borderBottom: '1px solid #F1F5F9', paddingBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ padding: 10, background: '#EEF2FF', borderRadius: 10, border: '1px solid #C7D2FE' }}>
                <FileText size={20} color="#4F46E5" />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0F172A', margin: 0 }}>
                    {activeJob.filename || 'Active Document'}
                  </h3>
                  <span style={{ fontSize: 11, color: '#64748B', fontWeight: 600 }} className="mono">
                    ID: {activeJob.job_id}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 2, fontSize: 12, color: '#64748B' }}>
                  <span>{activeJob.type || 'DOCUMENT_EXTRACTION'}</span>
                  <span>•</span>
                  <span>{activeJob.totalRows || 1} Document Unit</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span className={`badge ${isCompleted ? 'badge-success' : isFailed ? 'badge-error' : activeJob.status === 'WaitingForReview' ? 'badge-warning' : 'badge-indigo'}`}>
                {activeJob.status || 'PROCESSING'}
              </span>
              {(isCompleted || activeJob.status === 'WaitingForReview' || isFailed) && onNavigate && (
                <button
                  onClick={() => onNavigate('results')}
                  className="btn-primary"
                  style={{ fontSize: 13, padding: '0.5rem 1rem' }}
                >
                  <span>{isFailed ? 'View Job Errors' : 'View Results'}</span> <ArrowRight size={14} />
                </button>
              )}
            </div>
          </div>

          {/* Failure Banner if Job Failed */}
          {isFailed && activeJob.error && (
            <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 8, padding: '10px 14px', color: '#991B1B', fontSize: 13, fontWeight: 500 }}>
              <strong>Extraction Error:</strong> {activeJob.error}
            </div>
          )}

          {/* Progress Bar */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 700, color: isFailed ? '#DC2626' : '#4F46E5', marginBottom: 6 }}>
              <span>{isFailed ? 'Extraction Terminated' : 'Extraction Progress'}</span>
              <span>{progress}%</span>
            </div>
            <div style={{ height: 8, background: '#F1F5F9', borderRadius: 9999, overflow: 'hidden' }}>
              <div style={{ height: '100%', background: isFailed ? '#DC2626' : activeJob.status === 'WaitingForReview' ? '#F59E0B' : '#4F46E5', width: `${progress}%`, borderRadius: 9999, transition: 'width 0.3s ease' }} />
            </div>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: '#64748B' }}>
          <Sparkles size={28} color="#94A3B8" style={{ marginBottom: 8 }} />
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0F172A', margin: 0 }}>No Active Job in Queue</h3>
          <p style={{ fontSize: 13, margin: '4px 0 0' }}>Upload a file on the Upload page to start tracking live pipeline telemetry.</p>
        </div>
      )}

      {/* Multi-Worker Agent Grid */}
      <div>
        <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0F172A', margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
          <Cpu size={16} color="#4F46E5" />
          <span>Active Agentic Workers</span>
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {displayWorkers.map((w) => (
            <div key={w.id} className="card card-hover" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: 9999, background: w.status === 'RUNNING' ? '#10B981' : '#94A3B8' }} />
                  <span style={{ fontSize: 14, fontWeight: 700, color: '#0F172A' }}>Worker #{w.id} — {w.name}</span>
                </div>
                <span className="badge badge-neutral">{w.stage}</span>
              </div>

              <div style={{ fontSize: 12, color: '#475569', background: '#F8FAFC', padding: '8px 12px', borderRadius: 6, border: '1px solid #E2E8F0' }}>
                <div style={{ fontWeight: 700, color: '#4F46E5', marginBottom: 2 }}>{w.currentTask}</div>
                <div style={{ fontSize: 11, color: '#64748B' }}>{w.lastLog}</div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12, color: '#64748B', fontWeight: 500 }}>
                <span>Model: <strong style={{ color: '#0F172A' }}>{w.modelUsed}</strong></span>
                <span>Confidence: <strong style={{ color: '#059669' }}>{w.confidence}%</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Terminal Log Stream */}
      <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, borderBottom: '1px solid #F1F5F9', paddingBottom: 10 }}>
          <Terminal size={16} color="#4F46E5" />
          <h3 style={{ fontSize: 14, fontWeight: 700, color: '#0F172A', margin: 0 }}>Agentic Pipeline Execution Log Telemetry</h3>
        </div>

        <div className="mono" style={{
          background: '#0F172A',
          borderRadius: 8,
          padding: '1rem',
          maxHeight: 260,
          overflowY: 'auto',
          fontSize: 12,
          lineHeight: 1.6,
          color: '#E2E8F0',
        }}>
          {logs && logs.length > 0 ? (
            logs.map((l, idx) => (
              <div key={idx} style={{ marginBottom: 3 }}>
                <span style={{ color: '#64748B' }}>[{l.timestamp || 'LOG'}]</span>{' '}
                <span style={{ color: l.level === 'ERROR' ? '#F87171' : l.level === 'WARN' ? '#FBBF24' : '#818CF8', fontWeight: 700 }}>
                  [{l.level || 'INFO'}]
                </span>{' '}
                <span>{l.message}</span>
              </div>
            ))
          ) : (
            <div style={{ color: '#94A3B8' }}>
              [SYSTEM] Telemetry log stream initialized. Waiting for backend agent events...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
