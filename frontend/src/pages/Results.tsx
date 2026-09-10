import React, { useState } from 'react';
import type { UniversalDocumentDataset } from '../types';
import { Search, Download, RefreshCw, CheckCircle2, FileSpreadsheet, Database } from 'lucide-react';
import { getApiUrl } from '../config/api';

interface ResultsProps {
  dataset: UniversalDocumentDataset;
  onRefresh: () => void;
  activeJob?: any | null;
  allJobs?: any[];
  onSelectJob?: (jobId: string) => void;
}

export const Results: React.FC<ResultsProps> = ({ 
  dataset, 
  onRefresh,
  activeJob,
  allJobs = [],
  onSelectJob
}) => {
  const [searchTerm, setSearchTerm] = useState<string>("");

  const activeSchema = activeJob?.schema && activeJob.schema.length > 0 ? activeJob.schema : dataset?.schema || [];
  const activeRows = activeJob?.rows && activeJob.rows.length > 0 ? activeJob.rows : dataset?.rows || [];

  const filteredRows = activeRows.filter((r: any) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return Object.values(r.fields || {}).some(val => 
      String(val || '').toLowerCase().includes(term)
    );
  });

  const downloadFormat = (format: 'excel' | 'csv' | 'json') => {
    const jobId = activeJob?.job_id;
    let targetUrl = getApiUrl('/api/excel-rows');
    if (jobId) {
      targetUrl = getApiUrl(`/api/jobs/${jobId}/download/${format}`);
    }
    const a = document.createElement("a");
    a.href = targetUrl;
    a.download = `extracted_results_${jobId || 'export'}.${format === 'excel' ? 'xlsx' : format}`;
    a.click();
  };

  return (
    <div style={{ padding: '2rem', maxWidth: 1400, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: 22, fontWeight: 800, color: '#0F172A', margin: 0, letterSpacing: '-0.02em' }}>
              Extracted Results &amp; Dynamic Data Grid
            </h2>
            <span style={{ width: 8, height: 8, borderRadius: 9999, background: '#10B981' }} title="Live Socket Sync"></span>
          </div>
          <p style={{ fontSize: 13, color: '#64748B', margin: 0, marginTop: 2, fontWeight: 500 }}>
            Real-time synchronized data grid constructed dynamically from agentic schema
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Job Selector Dropdown */}
          {allJobs.length > 0 && onSelectJob && (
            <select
              value={activeJob?.job_id || ""}
              onChange={(e) => onSelectJob(e.target.value)}
              className="input-light"
              style={{ width: 'auto', padding: '0.6rem 1rem', fontSize: 12, fontWeight: 700 }}
            >
              {allJobs.map((j) => (
                <option key={j.job_id} value={j.job_id}>
                  {j.filename || 'Job'} ({j.job_id}) — {j.status}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={onRefresh}
            className="btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <RefreshCw size={14} />
            <span>Sync Data</span>
          </button>

          <button
            onClick={() => downloadFormat('excel')}
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <FileSpreadsheet size={16} />
            <span>Export Excel (.xlsx)</span>
          </button>

          <button
            onClick={() => downloadFormat('csv')}
            className="btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Download size={14} />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="card" style={{ padding: '1rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', minWidth: 280, flex: 1 }}>
          <Search size={16} color="#64748B" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search extracted fields, invoice numbers, values..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-light"
            style={{ paddingLeft: 38 }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 12, color: '#64748B', fontWeight: 600 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Database size={14} color="#4F46E5" />
            <span>{filteredRows.length} of {activeRows.length} Rows</span>
          </div>
          <span style={{ color: '#E2E8F0' }}>|</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <CheckCircle2 size={14} color="#059669" />
            <span>{activeSchema.length} Schema Columns</span>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="card" style={{ overflow: 'hidden' }}>
        {filteredRows.length > 0 && activeSchema.length > 0 ? (
          <div style={{ overflowX: 'auto', width: '100%' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 60 }}>#</th>
                  {activeSchema.map((col: any) => (
                    <th key={col.key}>{col.label || col.key}</th>
                  ))}
                  <th style={{ width: 100 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row: any) => (
                  <tr key={row.rowIndex || row.row_index || Math.random()}>
                    <td style={{ fontWeight: 700, color: '#4F46E5' }}>#{row.rowIndex || row.row_index}</td>
                    {activeSchema.map((col: any) => {
                      const val = row.fields ? row.fields[col.key] : row[col.key];
                      const displayVal = val !== undefined && val !== null ? String(val) : '-';
                      return (
                        <td key={col.key} title={displayVal}>
                          {displayVal}
                        </td>
                      );
                    })}
                    <td>
                      <span className={`badge ${row.status === 'COMPLETED' ? 'badge-success' : 'badge-warning'}`}>
                        {row.status || 'COMPLETED'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '4rem 2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <Database size={36} color="#94A3B8" />
            <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0F172A', margin: 0 }}>No Extracted Data Rows</h3>
            <p style={{ fontSize: 13, color: '#64748B', margin: 0, maxWidth: 400 }}>
              Upload a document on the Upload page to trigger multimodal schema generation &amp; live extraction.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
