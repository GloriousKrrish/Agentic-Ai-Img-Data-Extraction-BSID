import React, { useState } from 'react';
import type { UniversalDocumentDataset } from '../types';
import { Search, Download, RefreshCw, CheckCircle2, FileSpreadsheet, Database, Edit3, X, Save, ExternalLink, Check, AlertCircle, Brain, XCircle, CheckCircle } from 'lucide-react';
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
  const [selectedRow, setSelectedRow] = useState<any | null>(null);
  const [editedFields, setEditedFields] = useState<Record<string, string>>({});
  const [savingRow, setSavingRow] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

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

  const handleOpenRowEditor = (row: any) => {
    setSelectedRow(row);
    const initialFields = row.fields ? { ...row.fields } : {};
    setEditedFields(initialFields);
    setSaveSuccess(false);
  };

  const handleFieldChange = (key: string, value: string) => {
    setEditedFields(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveRow = async () => {
    if (!selectedRow || !activeJob?.job_id) return;
    setSavingRow(true);
    setSaveSuccess(false);
    const rowIndex = selectedRow.rowIndex || selectedRow.row_index || 1;
    try {
      const res = await fetch(getApiUrl(`/api/jobs/${activeJob.job_id}/rows/${rowIndex}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fields: editedFields })
      });
      if (res.ok) {
        setSaveSuccess(true);
        onRefresh();
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (err) {
      console.error('Save row error:', err);
    } finally {
      setSavingRow(false);
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: 1400, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

      {/* Phase 4: Schema Validation Panel — shown when job has schemaValidation data */}
      {activeJob?.schemaValidation && Object.keys(activeJob.schemaValidation).length > 0 && (
        <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.25rem', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <div style={{ width: 34, height: 34, borderRadius: 10, background: 'linear-gradient(135deg,#4F46E5,#7C3AED)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Brain size={18} color="white" />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: 14, color: '#0F172A' }}>Schema Validation Report <span style={{ fontSize: 11, fontWeight: 500, color: '#94A3B8', marginLeft: 6 }}>Phase 4</span></div>
              <div style={{ fontSize: 12, color: '#64748B' }}>{activeJob.schemaValidation.schema_name || 'Custom Schema'} · v{activeJob.schemaValidation.schema_version || '1.0.0'}</div>
            </div>
            {activeJob.schemaValidation.hitl_required ? (
              <span style={{ marginLeft: 'auto', padding: '4px 10px', borderRadius: 999, background: '#FEF3C7', color: '#D97706', fontSize: 11, fontWeight: 700, border: '1px solid #FDE68A' }}>HITL Required</span>
            ) : (
              <span style={{ marginLeft: 'auto', padding: '4px 10px', borderRadius: 999, background: '#ECFDF5', color: '#10B981', fontSize: 11, fontWeight: 700, border: '1px solid #A7F3D0' }}>Auto-Complete</span>
            )}
          </div>

          {/* KPI Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 16 }}>
            {[
              { label: 'COMPLETENESS', value: `${activeJob.schemaValidation.completeness_pct ?? 0}%`, color: '#4F46E5' },
              { label: 'QUALITY SCORE', value: `${((activeJob.schemaValidation.quality_score ?? 0) * 100).toFixed(1)}%`, color: '#7C3AED' },
              { label: 'MISSING REQUIRED', value: activeJob.schemaValidation.missing_required?.length ?? 0, color: activeJob.schemaValidation.missing_required?.length ? '#EF4444' : '#10B981' },
              { label: 'RULES FAILED', value: activeJob.schemaValidation.cross_field_rules_failed ?? 0, color: activeJob.schemaValidation.cross_field_rules_failed ? '#D97706' : '#10B981' },
            ].map(kpi => (
              <div key={kpi.label} style={{ background: '#F8FAFC', borderRadius: 10, padding: '0.75rem', textAlign: 'center' }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: '#94A3B8', letterSpacing: '0.06em' }}>{kpi.label}</div>
                <div style={{ fontSize: 22, fontWeight: 800, color: kpi.color, marginTop: 4 }}>{String(kpi.value)}</div>
              </div>
            ))}
          </div>

          {/* HITL Reasons */}
          {activeJob.schemaValidation.hitl_reasons?.length > 0 && (
            <div style={{ marginBottom: 12, padding: '0.6rem 0.85rem', background: '#FEF3C7', borderRadius: 8, border: '1px solid #FDE68A' }}>
              {activeJob.schemaValidation.hitl_reasons.map((r: string, i: number) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#92400E' }}>
                  <AlertCircle size={12} />{r}
                </div>
              ))}
            </div>
          )}

          {/* Field Outcomes Table */}
          {activeJob.schemaValidation.field_outcomes?.length > 0 && (
            <div style={{ maxHeight: 200, overflowY: 'auto', border: '1px solid #F1F5F9', borderRadius: 8 }}>
              {activeJob.schemaValidation.field_outcomes.map((fo: any, i: number) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '6px 12px',
                  borderBottom: i < activeJob.schemaValidation.field_outcomes.length - 1 ? '1px solid #F1F5F9' : 'none',
                  background: fo.passed ? 'transparent' : '#FFF8F8'
                }}>
                  {fo.passed ? <CheckCircle size={13} color="#10B981" /> : <XCircle size={13} color="#EF4444" />}
                  <span style={{ fontFamily: 'monospace', fontSize: 12, fontWeight: 600, color: '#475569', minWidth: 140 }}>{fo.field_key}</span>
                  {fo.value !== null && fo.value !== undefined && (
                    <span style={{ fontSize: 12, color: '#0F172A', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{String(fo.value)}</span>
                  )}
                  {fo.error && <span style={{ fontSize: 11, color: '#EF4444', marginLeft: 'auto', flexShrink: 0 }}>{fo.error}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: 22, fontWeight: 800, color: '#0F172A', margin: 0, letterSpacing: '-0.02em' }}>
              Extracted Results &amp; Human-in-the-Loop Console
            </h2>
            <span style={{ width: 8, height: 8, borderRadius: 9999, background: '#10B981' }} title="Live Socket Sync"></span>
          </div>
          <p style={{ fontSize: 13, color: '#64748B', margin: 0, marginTop: 2, fontWeight: 500 }}>
            Real-time data grid with side-by-side verification and row-level editing
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
                  <th style={{ width: 50 }}>#</th>
                  <th style={{ width: 70 }}>Action</th>
                  {activeSchema.map((col: any) => (
                    <th key={col.key}>{col.label || col.key}</th>
                  ))}
                  <th style={{ width: 110 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row: any) => (
                  <tr key={row.rowIndex || row.row_index || Math.random()} style={{ cursor: 'pointer' }} onClick={() => handleOpenRowEditor(row)}>
                    <td style={{ fontWeight: 700, color: '#4F46E5' }}>#{row.rowIndex || row.row_index}</td>
                    <td>
                      <button 
                        className="btn-secondary" 
                        style={{ padding: '0.25rem 0.5rem', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}
                        onClick={(e) => { e.stopPropagation(); handleOpenRowEditor(row); }}
                      >
                        <Edit3 size={12} />
                        <span>Verify</span>
                      </button>
                    </td>
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
                      <span className={`badge ${row.status === 'HUMAN_VERIFIED' ? 'badge-success' : row.status === 'COMPLETED' ? 'badge-success' : 'badge-warning'}`}>
                        {row.status || 'COMPLETED'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : activeJob?.status === 'Failed' ? (
          <div style={{ padding: '4rem 2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <XCircle size={42} color="#EF4444" />
            <h3 style={{ fontSize: 16, fontWeight: 700, color: '#991B1B', margin: 0 }}>Extraction Failed</h3>
            <p style={{ fontSize: 13, color: '#DC2626', margin: 0, maxWidth: 500, background: '#FEF2F2', padding: '12px 18px', borderRadius: 8, border: '1px solid #FECACA' }}>
              {activeJob.error || 'Document processing was terminated due to an internal error or missing API key.'}
            </p>
          </div>
        ) : activeJob && !['Completed', 'Failed', 'WaitingForReview'].includes(activeJob.status) ? (
          <div style={{ padding: '4rem 2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <RefreshCw size={36} color="#4F46E5" style={{ animation: 'spin 1.5s linear infinite' }} />
            <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0F172A', margin: 0 }}>Extraction In Progress</h3>
            <p style={{ fontSize: 13, color: '#64748B', margin: 0, maxWidth: 400 }}>
              Stage: {activeJob.current_stage || 'Processing document fields'} ({activeJob.progress || 0}%)
            </p>
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

      {/* Human-in-the-Loop Side-by-Side Review Drawer / Modal */}
      {selectedRow && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          backdropFilter: 'blur(4px)',
          zIndex: 999,
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <div style={{
            width: '100%',
            maxWidth: 850,
            height: '100%',
            backgroundColor: '#FFFFFF',
            boxShadow: '-10px 0 25px rgba(0,0,0,0.15)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{ padding: '1.25rem 1.5rem', background: '#0F172A', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 17, fontWeight: 800 }}>
                  HITL Verification — Row #{selectedRow.rowIndex || selectedRow.row_index || 1}
                </h3>
                <p style={{ margin: 0, fontSize: 12, color: '#94A3B8', marginTop: 2 }}>
                  Side-by-side inspection &amp; instant field value override
                </p>
              </div>
              <button onClick={() => setSelectedRow(null)} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            {/* Modal Body: Form + Preview Link */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {saveSuccess && (
                <div style={{ padding: '0.8rem 1rem', background: '#ECFDF5', border: '1px solid #10B981', borderRadius: 8, color: '#065F46', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Check size={16} />
                  <span>Fields updated successfully! SQLite state and export datasets updated.</span>
                </div>
              )}

              {/* Source Document Link / Info */}
              {(selectedRow.fields?.invoiceImageLink || selectedRow.fields?.url) && (
                <div style={{ padding: '0.8rem 1rem', background: '#F8FAFC', borderRadius: 8, border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#475569' }}>Source Document Link</span>
                  <a 
                    href={selectedRow.fields.invoiceImageLink || selectedRow.fields.url} 
                    target="_blank" 
                    rel="noreferrer" 
                    style={{ fontSize: 12, color: '#4F46E5', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    <span>View Image Document</span>
                    <ExternalLink size={12} />
                  </a>
                </div>
              )}

              {/* Editable Fields Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
                {activeSchema.map((col: any) => {
                  const key = col.key;
                  const label = col.label || key;
                  const currentVal = editedFields[key] !== undefined ? editedFields[key] : (selectedRow.fields ? selectedRow.fields[key] : selectedRow[key]) || "";

                  return (
                    <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <label style={{ fontSize: 12, fontWeight: 700, color: '#334155' }}>
                        {label} <span style={{ fontSize: 11, color: '#94A3B8', fontWeight: 500 }}>({key})</span>
                      </label>
                      <input
                        type="text"
                        value={currentVal}
                        onChange={(e) => handleFieldChange(key, e.target.value)}
                        className="input-light"
                        style={{ fontSize: 13, padding: '0.6rem 0.8rem' }}
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '1rem 1.5rem', background: '#F8FAFC', borderTop: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 10 }}>
              <button onClick={() => setSelectedRow(null)} className="btn-secondary" style={{ padding: '0.6rem 1.2rem' }}>
                Cancel
              </button>
              <button 
                onClick={handleSaveRow} 
                disabled={savingRow} 
                className="btn-primary" 
                style={{ padding: '0.6rem 1.5rem', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <Save size={16} />
                <span>{savingRow ? 'Saving...' : 'Save & Overwrite Row'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
