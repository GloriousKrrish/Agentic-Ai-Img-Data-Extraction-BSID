import React from 'react';
import type { SystemKPIs, UniversalDocumentDataset } from '../types';
import { Upload, Table, Clock, Activity, FileText, ArrowRight, ShieldCheck, Bot } from 'lucide-react';

interface DashboardProps {
  kpis: SystemKPIs;
  dataset: UniversalDocumentDataset;
  onNavigate: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ kpis, dataset, onNavigate }) => {
  const isEngineActive = kpis.pendingDocuments > 0;
  const schema = dataset?.schema || [];
  const rows = dataset?.rows || [];

  const statCards = [
    {
      title: 'TOTAL DOCUMENTS',
      value: kpis.totalDocuments.toLocaleString(),
      sub: 'Processed this session',
      icon: FileText,
      color: '#4F46E5',
    },
    {
      title: 'EXTRACTION ACCURACY',
      value: `${kpis.successRate.toFixed(1)}%`,
      sub: 'Zero schema errors',
      icon: ShieldCheck,
      color: '#059669',
    },
    {
      title: 'QUEUE PENDING',
      value: kpis.pendingDocuments.toString(),
      sub: isEngineActive ? 'Processing active' : 'All jobs completed',
      icon: Clock,
      color: '#D97706',
    },
    {
      title: 'EXTRACTED RECORDS',
      value: (dataset?.rows?.length || 0).toString(),
      sub: 'Live dataset rows',
      icon: Table,
      color: '#2563EB',
    },
  ];

  return (
    <div style={{ padding: '2rem', maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header Banner */}
      <div className="card" style={{
        padding: '1.75rem 2rem',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1.25rem',
      }}>
        <div>
          <div className="badge badge-indigo" style={{ marginBottom: 10 }}>
            <Bot size={14} style={{ marginRight: 4 }} />
            Multimodal Document Intelligence Engine
          </div>
          
          <h1 style={{ fontSize: 24, fontWeight: 800, color: '#0F172A', margin: 0, letterSpacing: '-0.025em' }}>
            Agentic AI Data Extraction Dashboard
          </h1>
          
          <p style={{ fontSize: 13, color: '#64748B', margin: 0, marginTop: 4, maxWidth: 580, fontWeight: 500 }}>
            Real-time multimodal extraction, OpenCV adaptive preprocessing &amp; automatic dynamic schema discovery.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className={isEngineActive ? 'badge badge-success' : 'badge badge-neutral'} style={{ padding: '6px 12px' }}>
            <span style={{ 
              width: 8, 
              height: 8, 
              borderRadius: 9999, 
              background: isEngineActive ? '#10B981' : '#94A3B8', 
              marginRight: 6
            }}></span>
            {isEngineActive ? 'Engine Active' : 'Engine Idle'}
          </div>

          <button
            onClick={() => onNavigate('upload')}
            className="btn-primary"
          >
            <Upload size={16} />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div key={i} className="stat-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#64748B', letterSpacing: '0.05em' }}>{card.title}</span>
                <div style={{ 
                  width: 34, 
                  height: 34, 
                  borderRadius: 8, 
                  background: `${card.color}10`, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  border: `1px solid ${card.color}25` 
                }}>
                  <Icon size={18} color={card.color} />
                </div>
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: '#0F172A', letterSpacing: '-0.025em', lineHeight: 1 }}>
                {card.value}
              </div>
              <div style={{ fontSize: 12, color: '#64748B', marginTop: 6, fontWeight: 500 }}>
                {card.sub}
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Navigation Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.25rem' }}>
        <div
          onClick={() => onNavigate('upload')}
          className="card card-hover"
          style={{ padding: '1.5rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 12 }}
        >
          <div style={{ width: 40, height: 40, borderRadius: 10, background: '#EEF2FF', border: '1px solid #C7D2FE', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Upload size={20} color="#4F46E5" />
          </div>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0F172A', margin: 0 }}>Drop Anything Here</h3>
            <p style={{ fontSize: 12, color: '#64748B', margin: '4px 0 0', lineHeight: 1.4 }}>Upload PDFs, Images, Invoices, Excel, CSV or ZIP archives</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#4F46E5', marginTop: 'auto' }}>
            <span>Start Extracting</span> <ArrowRight size={14} />
          </div>
        </div>

        <div
          onClick={() => onNavigate('processing')}
          className="card card-hover"
          style={{ padding: '1.5rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 12 }}
        >
          <div style={{ width: 40, height: 40, borderRadius: 10, background: '#F0FDF4', border: '1px solid #BBF7D0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Activity size={20} color="#16A34A" />
          </div>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0F172A', margin: 0 }}>Live Telemetry &amp; Logs</h3>
            <p style={{ fontSize: 12, color: '#64748B', margin: '4px 0 0', lineHeight: 1.4 }}>Monitor multi-agent execution, OCR &amp; VLM step-by-step logs</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#16A34A', marginTop: 'auto' }}>
            <span>Inspect Pipeline</span> <ArrowRight size={14} />
          </div>
        </div>

        <div
          onClick={() => onNavigate('results')}
          className="card card-hover"
          style={{ padding: '1.5rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 12 }}
        >
          <div style={{ width: 40, height: 40, borderRadius: 10, background: '#EFF6FF', border: '1px solid #BFDBFE', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Table size={20} color="#2563EB" />
          </div>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0F172A', margin: 0 }}>Dynamic Data Grid</h3>
            <p style={{ fontSize: 12, color: '#64748B', margin: '4px 0 0', lineHeight: 1.4 }}>View, filter, search &amp; export auto-discovered table schemas</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#2563EB', marginTop: 'auto' }}>
            <span>Explore Results</span> <ArrowRight size={14} />
          </div>
        </div>
      </div>

      {/* Extracted Stream Preview */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #F1F5F9', paddingBottom: '1rem', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0F172A', margin: 0 }}>Extracted Dataset Stream</h3>
            <p style={{ fontSize: 12, color: '#64748B', margin: '2px 0 0' }}>Auto-discovered schema columns &amp; live extracted records</p>
          </div>
          <button onClick={() => onNavigate('results')} className="btn-secondary" style={{ fontSize: 12, padding: '5px 12px' }}>
            View Full Dataset ({rows.length})
          </button>
        </div>

        {rows.length > 0 && schema.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Row #</th>
                  {schema.slice(0, 5).map(col => (
                    <th key={col.key}>{col.label}</th>
                  ))}
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 5).map((row) => (
                  <tr key={row.rowIndex}>
                    <td style={{ fontWeight: 700, color: '#4F46E5' }}>#{row.rowIndex}</td>
                    {schema.slice(0, 5).map(col => (
                      <td key={col.key}>
                        {String(row.fields[col.key] || '-')}
                      </td>
                    ))}
                    <td>
                      <span className={`badge ${row.status === 'COMPLETED' ? 'badge-success' : 'badge-warning'}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '3rem 0', textAlign: 'center', color: '#64748B', fontSize: 13, fontWeight: 500 }}>
            No extracted rows yet. Upload a document or Excel batch to begin extraction.
          </div>
        )}
      </div>
    </div>
  );
};
