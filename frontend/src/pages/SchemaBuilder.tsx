import React, { useState, useEffect } from 'react';
import {
  Brain, Plus, Trash2, Save, Play, Upload, Download, ChevronDown, ChevronUp,
  Code, Type, Hash, Calendar, ToggleLeft, List, Layers, Link2, AlertCircle,
  CheckCircle, XCircle, RefreshCw, Copy, FileJson, Sparkles, Database,
  Edit3, Eye, GitCompare, Info
} from 'lucide-react';
import { getApiUrl } from '../config/api';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────
interface SchemaField {
  key: string;
  label: string;
  field_type: string;
  required: boolean;
  description: string;
  extraction_hint: string;
  regex_pattern: string | null;
  min_value: number | null;
  max_value: number | null;
  allowed_values: string[];
  default_value: string | null;
  confidence_threshold: number;
}

interface CrossFieldRule {
  rule_id?: string;
  formula: string;
  description: string;
  error_message: string;
  severity: 'error' | 'warning' | 'info';
  fields_involved: string[];
}

interface SavedSchema {
  schema_id: string;
  name: string;
  version: string;
  domain: string;
  description: string;
  fields?: SchemaField[];
  cross_field_rules?: CrossFieldRule[];
  created_at?: string;
  updated_at?: string;
  created_by?: string;
}

const FIELD_TYPES = [
  { value: 'string', label: 'Text (String)', icon: Type },
  { value: 'number', label: 'Number', icon: Hash },
  { value: 'date', label: 'Date', icon: Calendar },
  { value: 'boolean', label: 'Boolean', icon: ToggleLeft },
  { value: 'array', label: 'Array / List', icon: List },
  { value: 'object', label: 'Object / Dict', icon: Layers },
  { value: 'currency', label: 'Currency', icon: Hash },
  { value: 'percentage', label: 'Percentage', icon: Hash },
];

const DOMAIN_OPTIONS = [
  'invoice', 'medical', 'kyc', 'academic', 'financial', 'legal', 'custom'
];

const SEVERITIES = ['error', 'warning', 'info'];

// ─────────────────────────────────────────────────────────────────────────────
// Empty defaults
// ─────────────────────────────────────────────────────────────────────────────
const emptyField = (): SchemaField => ({
  key: '', label: '', field_type: 'string', required: false,
  description: '', extraction_hint: '', regex_pattern: null,
  min_value: null, max_value: null, allowed_values: [], default_value: null,
  confidence_threshold: 0.65
});

const emptyRule = (): CrossFieldRule => ({
  formula: '', description: '', error_message: '', severity: 'warning',
  fields_involved: []
});

// ─────────────────────────────────────────────────────────────────────────────
// Pill badge
// ─────────────────────────────────────────────────────────────────────────────
const Badge: React.FC<{ children: React.ReactNode; color?: string }> = ({ children, color = '#4F46E5' }) => (
  <span style={{
    fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 9999,
    background: `${color}18`, color, border: `1px solid ${color}40`
  }}>{children}</span>
);

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────
export const SchemaBuilder: React.FC = () => {
  // Tabs: build | saved | test
  const [activeSection, setActiveSection] = useState<'build' | 'saved' | 'test'>('build');

  // Schema state
  const [schemaName, setSchemaName] = useState('My Custom Schema');
  const [schemaDomain, setSchemaDomain] = useState('custom');
  const [schemaDesc, setSchemaDesc] = useState('');
  const [fields, setFields] = useState<SchemaField[]>([emptyField()]);
  const [rules, setRules] = useState<CrossFieldRule[]>([]);
  const [expandedField, setExpandedField] = useState<number | null>(0);
  const [expandedRule, setExpandedRule] = useState<number | null>(null);

  // NL input
  const [nlText, setNlText] = useState('');
  const [nlLoading, setNlLoading] = useState(false);

  // JSON import
  const [jsonInput, setJsonInput] = useState('');
  const [showJsonImport, setShowJsonImport] = useState(false);

  // Saved schemas
  const [savedSchemas, setSavedSchemas] = useState<SavedSchema[]>([]);
  const [selectedSaved, setSelectedSaved] = useState<SavedSchema | null>(null);

  // Test mode
  const [testFile, setTestFile] = useState<File | null>(null);
  const [testSchemaId, setTestSchemaId] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testLoading, setTestLoading] = useState(false);

  // Save state
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Load saved schemas on mount
  useEffect(() => {
    fetchSavedSchemas();
  }, []);

  const fetchSavedSchemas = async () => {
    try {
      const res = await fetch(getApiUrl('/api/schemas'));
      if (res.ok) setSavedSchemas(await res.json());
    } catch {}
  };

  // ── NL → Schema ─────────────────────────────────────────────────────────
  const convertNL = async () => {
    if (!nlText.trim()) return;
    setNlLoading(true);
    try {
      const res = await fetch(getApiUrl('/api/schemas/from-nl'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nl_text: nlText })
      });
      if (res.ok) {
        const data = await res.json();
        const s = data.schema;
        setSchemaName(s.name || 'NL-Generated Schema');
        setSchemaDomain(s.domain || 'custom');
        setSchemaDesc(s.description || '');
        setFields(s.fields?.length ? s.fields : [emptyField()]);
        setRules(s.cross_field_rules || []);
        setExpandedField(0);
      }
    } catch {}
    setNlLoading(false);
  };

  // ── JSON Import ──────────────────────────────────────────────────────────
  const importJSON = async () => {
    try {
      const parsed = JSON.parse(jsonInput);
      // Try inline ExtractionSchema format first
      if (parsed.fields) {
        setSchemaName(parsed.name || 'Imported Schema');
        setSchemaDomain(parsed.domain || 'custom');
        setSchemaDesc(parsed.description || '');
        setFields(parsed.fields.map((f: any) => ({ ...emptyField(), ...f, field_type: f.field_type || f.type || 'string' })));
        setRules(parsed.cross_field_rules || []);
      } else {
        // JSON Schema spec format
        const res = await fetch(getApiUrl('/api/schemas/from-json'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ json_schema: parsed })
        });
        if (res.ok) {
          const data = await res.json();
          const s = data.schema;
          setSchemaName(s.name || 'Imported Schema');
          setFields(s.fields || [emptyField()]);
        }
      }
      setShowJsonImport(false);
    } catch (e: any) {
      alert('Invalid JSON: ' + e.message);
    }
  };

  // ── Load Preset ──────────────────────────────────────────────────────────
  const loadPreset = async (presetName: string) => {
    try {
      const res = await fetch(getApiUrl('/api/schemas/presets'));
      if (res.ok) {
        const presets = await res.json();
        const preset = presets[presetName];
        if (preset) {
          setSchemaName(presetName);
          setSchemaDomain(preset.category?.toLowerCase() || 'custom');
          setFields(preset.fields?.map((f: any) => ({ ...emptyField(), ...f })) || [emptyField()]);
          setRules([]);
        }
      }
    } catch {}
  };

  // ── Field Helpers ────────────────────────────────────────────────────────
  const addField = () => {
    const newFields = [...fields, emptyField()];
    setFields(newFields);
    setExpandedField(newFields.length - 1);
  };

  const removeField = (idx: number) => {
    setFields(fields.filter((_, i) => i !== idx));
    if (expandedField === idx) setExpandedField(null);
  };

  const updateField = (idx: number, key: keyof SchemaField, value: any) => {
    const updated = [...fields];
    (updated[idx] as any)[key] = value;
    // Auto-generate key from label
    if (key === 'label' && typeof value === 'string') {
      const autoKey = value.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '').replace(/_(.)/g, (_, c) => c.toUpperCase());
      if (!updated[idx].key || updated[idx].key === updated[idx].label.replace(/\s+/g, '_').toLowerCase()) {
        updated[idx].key = autoKey.charAt(0).toLowerCase() + autoKey.slice(1);
      }
    }
    setFields(updated);
  };

  // ── Rule Helpers ─────────────────────────────────────────────────────────
  const addRule = () => {
    setRules([...rules, emptyRule()]);
    setExpandedRule(rules.length);
  };

  const removeRule = (idx: number) => {
    setRules(rules.filter((_, i) => i !== idx));
    if (expandedRule === idx) setExpandedRule(null);
  };

  const updateRule = (idx: number, key: keyof CrossFieldRule, value: any) => {
    const updated = [...rules];
    (updated[idx] as any)[key] = value;
    setRules(updated);
  };

  // ── Save Schema ──────────────────────────────────────────────────────────
  const saveSchema = async () => {
    setSaving(true);
    setValidationErrors([]);
    setSaveMsg('');
    try {
      const body = {
        name: schemaName, domain: schemaDomain, description: schemaDesc,
        fields: fields.filter(f => f.key),
        tables: [], cross_field_rules: rules, tags: []
      };
      const res = await fetch(getApiUrl('/api/schemas'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (res.ok) {
        setSaveMsg('✓ Schema saved successfully!');
        fetchSavedSchemas();
      } else {
        const errs = data.detail?.errors || [data.detail || 'Unknown error'];
        setValidationErrors(errs);
      }
    } catch (e: any) {
      setValidationErrors([e.message]);
    }
    setSaving(false);
    setTimeout(() => setSaveMsg(''), 3000);
  };

  // ── Load saved schema into editor ────────────────────────────────────────
  const loadSavedSchema = async (schemaId: string) => {
    try {
      const res = await fetch(getApiUrl(`/api/schemas/${schemaId}`));
      if (res.ok) {
        const s = await res.json();
        setSchemaName(s.name);
        setSchemaDomain(s.domain);
        setSchemaDesc(s.description || '');
        setFields(s.fields?.length ? s.fields.map((f: any) => ({ ...emptyField(), ...f })) : [emptyField()]);
        setRules(s.cross_field_rules || []);
        setActiveSection('build');
      }
    } catch {}
  };

  const deleteSchema = async (schemaId: string) => {
    if (!confirm('Delete this schema permanently?')) return;
    try {
      await fetch(getApiUrl(`/api/schemas/${schemaId}`), { method: 'DELETE' });
      fetchSavedSchemas();
    } catch {}
  };

  // ── Test Mode ────────────────────────────────────────────────────────────
  const runTest = async () => {
    if (!testFile || !testSchemaId) return;
    setTestLoading(true);
    setTestResult(null);
    try {
      const fd = new FormData();
      fd.append('file', testFile);
      const res = await fetch(getApiUrl(`/api/schemas/${testSchemaId}/validate-document`), {
        method: 'POST', body: fd
      });
      if (res.ok) setTestResult(await res.json());
    } catch {}
    setTestLoading(false);
  };

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────
  const sectionTabs = [
    { id: 'build', label: 'Schema Builder', icon: Brain },
    { id: 'saved', label: 'Saved Schemas', icon: Database },
    { id: 'test', label: 'Test Mode', icon: Play },
  ];

  return (
    <div style={{ padding: '1.5rem 2rem', maxWidth: 1100, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg,#4F46E5,#7C3AED)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(79,70,229,0.3)'
          }}>
            <Brain size={22} color="white" />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#0F172A' }}>
              Schema Builder <Badge color="#4F46E5">Phase 4</Badge>
            </h1>
            <p style={{ margin: 0, fontSize: 13, color: '#64748B', marginTop: 2 }}>
              Define custom extraction schemas using natural language, JSON, or the visual editor
            </p>
          </div>
        </div>
      </div>

      {/* Section Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: '1.5rem', background: '#F1F5F9', borderRadius: 10, padding: 4 }}>
        {sectionTabs.map(t => {
          const Icon = t.icon;
          const isActive = activeSection === t.id;
          return (
            <button key={t.id} onClick={() => setActiveSection(t.id as any)} style={{
              flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              padding: '0.55rem 1rem', borderRadius: 8,
              background: isActive ? '#FFFFFF' : 'transparent',
              color: isActive ? '#4F46E5' : '#64748B',
              fontWeight: isActive ? 700 : 500, fontSize: 13,
              border: isActive ? '1px solid #E2E8F0' : '1px solid transparent',
              boxShadow: isActive ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
              cursor: 'pointer', transition: 'all 0.15s'
            }}>
              <Icon size={15} />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* ── BUILD SECTION ── */}
      {activeSection === 'build' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.25rem' }}>
          {/* NL Input Panel */}
          <div style={{ background: 'linear-gradient(135deg,#EEF2FF,#F5F3FF)', border: '1px solid #C7D2FE', borderRadius: 14, padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <Sparkles size={16} color="#4F46E5" />
              <span style={{ fontWeight: 700, fontSize: 14, color: '#3730A3' }}>Natural Language → Schema Converter</span>
            </div>
            <textarea
              value={nlText}
              onChange={e => setNlText(e.target.value)}
              placeholder="Describe the fields you want to extract in plain English...&#10;&#10;Examples:&#10;• Extract invoice_number, invoice_date, vendor_name, customer_name, line_items, grand_total, GST&#10;• I need patient name, date of birth, diagnosis, lab results, doctor name&#10;• Extract contract title, party A, party B, effective date, contract value"
              rows={5}
              style={{
                width: '100%', borderRadius: 10, border: '1px solid #C7D2FE',
                padding: '0.75rem', fontSize: 13, fontFamily: 'inherit',
                background: '#FFFFFF', resize: 'vertical', outline: 'none', boxSizing: 'border-box'
              }}
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
              <button onClick={convertNL} disabled={nlLoading || !nlText.trim()} style={{
                display: 'flex', alignItems: 'center', gap: 6, padding: '0.55rem 1.25rem',
                background: '#4F46E5', color: 'white', borderRadius: 8, border: 'none',
                fontWeight: 700, fontSize: 13, cursor: 'pointer', opacity: nlLoading ? 0.7 : 1
              }}>
                {nlLoading ? <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Brain size={14} />}
                {nlLoading ? 'Converting...' : 'Convert to Schema'}
              </button>
              <button onClick={() => setShowJsonImport(v => !v)} style={{
                display: 'flex', alignItems: 'center', gap: 6, padding: '0.55rem 1.25rem',
                background: 'white', color: '#4F46E5', borderRadius: 8, border: '1px solid #C7D2FE',
                fontWeight: 600, fontSize: 13, cursor: 'pointer'
              }}>
                <FileJson size={14} />
                Import JSON
              </button>
              {/* Preset loader */}
              <select onChange={e => { if (e.target.value) loadPreset(e.target.value); e.target.value = ''; }}
                style={{
                  padding: '0.55rem 0.75rem', borderRadius: 8, border: '1px solid #C7D2FE',
                  background: 'white', color: '#4F46E5', fontSize: 13, cursor: 'pointer'
                }}>
                <option value="">Load Preset...</option>
                <option value="Invoice / Bill">Invoice / Bill</option>
                <option value="Medical / Lab Report">Medical / Lab Report</option>
                <option value="KYC / ID Card">KYC / ID Card</option>
                <option value="Academic Result / Marksheet">Academic Result</option>
                <option value="Financial Statement">Financial Statement</option>
                <option value="Legal Contract">Legal Contract</option>
              </select>
            </div>

            {/* JSON Import Panel */}
            {showJsonImport && (
              <div style={{ marginTop: 12, padding: 12, background: '#FFFFFF', borderRadius: 10, border: '1px solid #C7D2FE' }}>
                <p style={{ margin: '0 0 8px', fontSize: 12, color: '#64748B' }}>
                  Paste JSON Schema spec or raw ExtractionSchema JSON:
                </p>
                <textarea value={jsonInput} onChange={e => setJsonInput(e.target.value)}
                  rows={6} placeholder='{"properties": {"invoice_number": {"type": "string"}}}'
                  style={{
                    width: '100%', borderRadius: 8, border: '1px solid #E2E8F0',
                    padding: '0.6rem', fontSize: 12, fontFamily: 'monospace',
                    background: '#F8FAFC', resize: 'vertical', outline: 'none', boxSizing: 'border-box'
                  }}
                />
                <button onClick={importJSON} style={{
                  marginTop: 8, padding: '0.45rem 1rem', background: '#4F46E5', color: 'white',
                  borderRadius: 8, border: 'none', fontWeight: 700, fontSize: 12, cursor: 'pointer'
                }}>Import</button>
              </div>
            )}
          </div>

          {/* Schema Metadata */}
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.25rem' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 700, color: '#0F172A' }}>Schema Metadata</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 4 }}>Schema Name *</label>
                <input value={schemaName} onChange={e => setSchemaName(e.target.value)}
                  style={{ width: '100%', borderRadius: 8, border: '1px solid #E2E8F0', padding: '0.55rem 0.75rem', fontSize: 13, boxSizing: 'border-box', outline: 'none' }} />
              </div>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 4 }}>Domain</label>
                <select value={schemaDomain} onChange={e => setSchemaDomain(e.target.value)}
                  style={{ width: '100%', borderRadius: 8, border: '1px solid #E2E8F0', padding: '0.55rem 0.75rem', fontSize: 13 }}>
                  {DOMAIN_OPTIONS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
                </select>
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 4 }}>Description</label>
                <input value={schemaDesc} onChange={e => setSchemaDesc(e.target.value)}
                  placeholder="Optional: describe what this schema extracts"
                  style={{ width: '100%', borderRadius: 8, border: '1px solid #E2E8F0', padding: '0.55rem 0.75rem', fontSize: 13, boxSizing: 'border-box', outline: 'none' }} />
              </div>
            </div>
          </div>

          {/* Fields Editor */}
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#0F172A' }}>
                Schema Fields <Badge color="#4F46E5">{fields.length}</Badge>
              </h3>
              <button onClick={addField} style={{
                display: 'flex', alignItems: 'center', gap: 5, padding: '0.45rem 1rem',
                background: '#4F46E5', color: 'white', borderRadius: 8, border: 'none',
                fontWeight: 700, fontSize: 12, cursor: 'pointer'
              }}>
                <Plus size={13} /> Add Field
              </button>
            </div>

            {fields.map((f, idx) => (
              <div key={idx} style={{
                border: `1px solid ${expandedField === idx ? '#C7D2FE' : '#E2E8F0'}`,
                borderRadius: 10, marginBottom: 8, overflow: 'hidden',
                background: expandedField === idx ? '#F8FAFF' : '#FAFAFA'
              }}>
                {/* Field header row */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.65rem 1rem', cursor: 'pointer' }}
                  onClick={() => setExpandedField(expandedField === idx ? null : idx)}>
                  <div style={{
                    width: 26, height: 26, borderRadius: 6, background: f.required ? '#FEF3C7' : '#EEF2FF',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                  }}>
                    <Hash size={13} color={f.required ? '#D97706' : '#4F46E5'} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <span style={{ fontWeight: 700, fontSize: 13, color: '#0F172A' }}>{f.label || `Field ${idx + 1}`}</span>
                    {f.key && <span style={{ fontSize: 11, color: '#94A3B8', marginLeft: 8, fontFamily: 'monospace' }}>{f.key}</span>}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                    <Badge color={f.required ? '#D97706' : '#64748B'}>{f.required ? 'Required' : 'Optional'}</Badge>
                    <Badge color="#4F46E5">{f.field_type}</Badge>
                    <button onClick={e => { e.stopPropagation(); removeField(idx); }}
                      style={{ padding: 4, background: 'transparent', border: 'none', cursor: 'pointer', color: '#EF4444', borderRadius: 6 }}>
                      <Trash2 size={13} />
                    </button>
                    {expandedField === idx ? <ChevronUp size={14} color="#64748B" /> : <ChevronDown size={14} color="#64748B" />}
                  </div>
                </div>

                {/* Field expanded form */}
                {expandedField === idx && (
                  <div style={{ padding: '0 1rem 1rem', borderTop: '1px solid #E2E8F0' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 12 }}>
                      <div>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Display Label *</label>
                        <input value={f.label} onChange={e => updateField(idx, 'label', e.target.value)}
                          placeholder="e.g. Invoice Number"
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12, boxSizing: 'border-box', outline: 'none' }} />
                      </div>
                      <div>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Field Key (camelCase) *</label>
                        <input value={f.key} onChange={e => updateField(idx, 'key', e.target.value)}
                          placeholder="invoiceNumber"
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12, fontFamily: 'monospace', boxSizing: 'border-box', outline: 'none' }} />
                      </div>
                      <div>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Field Type</label>
                        <select value={f.field_type} onChange={e => updateField(idx, 'field_type', e.target.value)}
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12 }}>
                          {FIELD_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                        </select>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569' }}>Required Field</label>
                        <div onClick={() => updateField(idx, 'required', !f.required)}
                          style={{
                            width: 38, height: 22, borderRadius: 999, cursor: 'pointer', transition: 'all 0.2s',
                            background: f.required ? '#4F46E5' : '#E2E8F0', position: 'relative'
                          }}>
                          <div style={{
                            width: 16, height: 16, borderRadius: '50%', background: 'white',
                            position: 'absolute', top: 3, left: f.required ? 19 : 3, transition: 'all 0.2s',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
                          }} />
                        </div>
                      </div>
                      <div style={{ gridColumn: '1 / -1' }}>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Extraction Description</label>
                        <input value={f.description} onChange={e => updateField(idx, 'description', e.target.value)}
                          placeholder="How should the AI extract this field? e.g. The unique invoice reference number found at the top right of the document"
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12, boxSizing: 'border-box', outline: 'none' }} />
                      </div>
                      <div>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Extraction Hint (Location)</label>
                        <input value={f.extraction_hint} onChange={e => updateField(idx, 'extraction_hint', e.target.value)}
                          placeholder="e.g. Top-right corner, header section"
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12, boxSizing: 'border-box', outline: 'none' }} />
                      </div>
                      <div>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Regex Pattern (Optional)</label>
                        <input value={f.regex_pattern || ''} onChange={e => updateField(idx, 'regex_pattern', e.target.value || null)}
                          placeholder="e.g. ^\d{2}/\d{2}/\d{4}$"
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12, fontFamily: 'monospace', boxSizing: 'border-box', outline: 'none' }} />
                      </div>
                      {(f.field_type === 'number' || f.field_type === 'currency' || f.field_type === 'percentage') && (
                        <>
                          <div>
                            <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Min Value</label>
                            <input type="number" value={f.min_value ?? ''} onChange={e => updateField(idx, 'min_value', e.target.value ? parseFloat(e.target.value) : null)}
                              style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12, boxSizing: 'border-box', outline: 'none' }} />
                          </div>
                          <div>
                            <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Max Value</label>
                            <input type="number" value={f.max_value ?? ''} onChange={e => updateField(idx, 'max_value', e.target.value ? parseFloat(e.target.value) : null)}
                              style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12, boxSizing: 'border-box', outline: 'none' }} />
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {fields.length === 0 && (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#94A3B8', fontSize: 13 }}>
                No fields added yet. Use the NL converter above or click "Add Field".
              </div>
            )}
          </div>

          {/* Cross-Field Rules */}
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#0F172A' }}>
                  Cross-Field Validation Rules <Badge color="#7C3AED">{rules.length}</Badge>
                </h3>
                <p style={{ margin: '4px 0 0', fontSize: 12, color: '#64748B' }}>
                  Arithmetic or logical constraints between fields (e.g. <code style={{ background: '#F1F5F9', padding: '1px 4px', borderRadius: 4 }}>grand_total == subtotal + tax</code>)
                </p>
              </div>
              <button onClick={addRule} style={{
                display: 'flex', alignItems: 'center', gap: 5, padding: '0.45rem 1rem',
                background: '#7C3AED', color: 'white', borderRadius: 8, border: 'none',
                fontWeight: 700, fontSize: 12, cursor: 'pointer'
              }}>
                <Plus size={13} /> Add Rule
              </button>
            </div>

            {rules.map((r, idx) => (
              <div key={idx} style={{
                border: `1px solid ${expandedRule === idx ? '#DDD6FE' : '#E2E8F0'}`,
                borderRadius: 10, marginBottom: 8, overflow: 'hidden'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.65rem 1rem', cursor: 'pointer', background: '#FAFAFA' }}
                  onClick={() => setExpandedRule(expandedRule === idx ? null : idx)}>
                  <Code size={14} color="#7C3AED" />
                  <span style={{ flex: 1, fontFamily: 'monospace', fontSize: 12, color: '#3730A3' }}>{r.formula || `Rule ${idx + 1}`}</span>
                  <Badge color={r.severity === 'error' ? '#EF4444' : r.severity === 'warning' ? '#D97706' : '#3B82F6'}>{r.severity}</Badge>
                  <button onClick={e => { e.stopPropagation(); removeRule(idx); }}
                    style={{ padding: 4, background: 'transparent', border: 'none', cursor: 'pointer', color: '#EF4444', borderRadius: 6 }}>
                    <Trash2 size={13} />
                  </button>
                  {expandedRule === idx ? <ChevronUp size={14} color="#64748B" /> : <ChevronDown size={14} color="#64748B" />}
                </div>
                {expandedRule === idx && (
                  <div style={{ padding: '0 1rem 1rem', borderTop: '1px solid #E2E8F0' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 12 }}>
                      <div style={{ gridColumn: '1 / -1' }}>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Formula (Python expression)</label>
                        <input value={r.formula} onChange={e => updateRule(idx, 'formula', e.target.value)}
                          placeholder="grand_total == subtotal + tax"
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #DDD6FE', padding: '0.5rem 0.65rem', fontSize: 12, fontFamily: 'monospace', boxSizing: 'border-box', outline: 'none', background: '#F5F3FF' }} />
                      </div>
                      <div>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Description</label>
                        <input value={r.description} onChange={e => updateRule(idx, 'description', e.target.value)}
                          placeholder="Grand total must equal subtotal + tax"
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12, boxSizing: 'border-box', outline: 'none' }} />
                      </div>
                      <div>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Severity</label>
                        <select value={r.severity} onChange={e => updateRule(idx, 'severity', e.target.value)}
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12 }}>
                          {SEVERITIES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                        </select>
                      </div>
                      <div style={{ gridColumn: '1 / -1' }}>
                        <label style={{ fontSize: 11, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 3 }}>Error Message</label>
                        <input value={r.error_message} onChange={e => updateRule(idx, 'error_message', e.target.value)}
                          placeholder="Grand total does not match subtotal + tax"
                          style={{ width: '100%', borderRadius: 7, border: '1px solid #E2E8F0', padding: '0.5rem 0.65rem', fontSize: 12, boxSizing: 'border-box', outline: 'none' }} />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Save Controls */}
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.25rem', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <button onClick={saveSchema} disabled={saving} style={{
              display: 'flex', alignItems: 'center', gap: 7, padding: '0.65rem 1.5rem',
              background: 'linear-gradient(135deg,#4F46E5,#7C3AED)', color: 'white', borderRadius: 10,
              border: 'none', fontWeight: 700, fontSize: 14, cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(79,70,229,0.25)', opacity: saving ? 0.7 : 1
            }}>
              {saving ? <RefreshCw size={15} style={{ animation: 'spin 1s linear infinite' }} /> : <Save size={15} />}
              {saving ? 'Saving...' : 'Save Schema'}
            </button>

            {saveMsg && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#10B981', fontSize: 13, fontWeight: 600 }}>
                <CheckCircle size={16} />{saveMsg}
              </div>
            )}

            {validationErrors.length > 0 && (
              <div style={{ flex: 1, background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 8, padding: '0.5rem 0.75rem' }}>
                {validationErrors.map((e, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#DC2626', fontSize: 12 }}>
                    <AlertCircle size={12} />{e}
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginLeft: 'auto', fontSize: 12, color: '#94A3B8' }}>
              {fields.filter(f => f.key).length} fields · {rules.length} rules
            </div>
          </div>
        </div>
      )}

      {/* ── SAVED SCHEMAS ── */}
      {activeSection === 'saved' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#0F172A' }}>
              Saved Schemas <Badge color="#4F46E5">{savedSchemas.length}</Badge>
            </span>
            <button onClick={fetchSavedSchemas} style={{
              display: 'flex', alignItems: 'center', gap: 5, padding: '0.45rem 1rem',
              background: '#F1F5F9', color: '#475569', borderRadius: 8, border: '1px solid #E2E8F0',
              fontSize: 12, fontWeight: 600, cursor: 'pointer'
            }}>
              <RefreshCw size={13} /> Refresh
            </button>
          </div>

          {savedSchemas.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#94A3B8', background: '#FFFFFF', borderRadius: 14, border: '1px solid #E2E8F0' }}>
              <Database size={32} style={{ marginBottom: 12, opacity: 0.3 }} />
              <p style={{ margin: 0, fontSize: 14 }}>No schemas saved yet. Create one in the Schema Builder tab.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 12 }}>
              {savedSchemas.map(s => (
                <div key={s.schema_id} style={{
                  background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.1rem',
                  transition: 'all 0.15s', cursor: 'pointer'
                }}
                  onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.border = '1px solid #C7D2FE'}
                  onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.border = '1px solid #E2E8F0'}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 14, color: '#0F172A' }}>{s.name}</div>
                      <div style={{ fontSize: 11, color: '#94A3B8', marginTop: 2, fontFamily: 'monospace' }}>{s.schema_id}</div>
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <Badge color="#4F46E5">v{s.version}</Badge>
                      <Badge color="#7C3AED">{s.domain}</Badge>
                    </div>
                  </div>
                  {s.description && <p style={{ margin: '0 0 10px', fontSize: 12, color: '#64748B' }}>{s.description}</p>}
                  <div style={{ fontSize: 11, color: '#94A3B8', marginBottom: 12 }}>
                    Updated: {new Date(s.updated_at || '').toLocaleDateString()} · Created by: {s.created_by}
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <button onClick={() => loadSavedSchema(s.schema_id)} style={{
                      display: 'flex', alignItems: 'center', gap: 5, padding: '0.4rem 0.85rem',
                      background: '#EEF2FF', color: '#4F46E5', borderRadius: 7, border: '1px solid #C7D2FE',
                      fontSize: 11, fontWeight: 700, cursor: 'pointer'
                    }}>
                      <Edit3 size={11} /> Edit
                    </button>
                    <button onClick={() => { setTestSchemaId(s.schema_id); setActiveSection('test'); }} style={{
                      display: 'flex', alignItems: 'center', gap: 5, padding: '0.4rem 0.85rem',
                      background: '#ECFDF5', color: '#10B981', borderRadius: 7, border: '1px solid #A7F3D0',
                      fontSize: 11, fontWeight: 700, cursor: 'pointer'
                    }}>
                      <Play size={11} /> Test
                    </button>
                    <button onClick={() => deleteSchema(s.schema_id)} style={{
                      display: 'flex', alignItems: 'center', gap: 5, padding: '0.4rem 0.85rem',
                      background: '#FEF2F2', color: '#EF4444', borderRadius: 7, border: '1px solid #FECACA',
                      fontSize: 11, fontWeight: 700, cursor: 'pointer'
                    }}>
                      <Trash2 size={11} /> Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── TEST MODE ── */}
      {activeSection === 'test' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', alignItems: 'start' }}>
          <div>
            <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.25rem' }}>
              <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 700, color: '#0F172A' }}>
                Schema Test Mode
              </h3>
              <p style={{ margin: '0 0 16px', fontSize: 12, color: '#64748B' }}>
                Upload a document and select a schema to run schema-constrained extraction and see the validation report.
              </p>

              <div style={{ marginBottom: 12 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>Select Schema</label>
                <select value={testSchemaId} onChange={e => setTestSchemaId(e.target.value)}
                  style={{ width: '100%', borderRadius: 8, border: '1px solid #E2E8F0', padding: '0.55rem 0.75rem', fontSize: 13 }}>
                  <option value="">-- Select a saved schema --</option>
                  {savedSchemas.map(s => <option key={s.schema_id} value={s.schema_id}>{s.name} (v{s.version})</option>)}
                </select>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>Upload Test Document</label>
                <label style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                  padding: '1.5rem', border: '2px dashed #C7D2FE', borderRadius: 10, cursor: 'pointer',
                  background: testFile ? '#ECFDF5' : '#F8FAFF', transition: 'all 0.15s'
                }}>
                  <input type="file" onChange={e => setTestFile(e.target.files?.[0] || null)} style={{ display: 'none' }} />
                  <Upload size={20} color={testFile ? '#10B981' : '#4F46E5'} />
                  <span style={{ fontSize: 12, color: testFile ? '#10B981' : '#64748B', marginTop: 6, fontWeight: 600 }}>
                    {testFile ? testFile.name : 'Click to upload document'}
                  </span>
                </label>
              </div>

              <button onClick={runTest} disabled={!testFile || !testSchemaId || testLoading}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '0.65rem', background: 'linear-gradient(135deg,#10B981,#059669)',
                  color: 'white', borderRadius: 10, border: 'none', fontWeight: 700, fontSize: 14,
                  cursor: !testFile || !testSchemaId ? 'not-allowed' : 'pointer',
                  opacity: !testFile || !testSchemaId ? 0.5 : 1
                }}>
                {testLoading ? <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={16} />}
                {testLoading ? 'Running extraction...' : 'Run Schema Test'}
              </button>
            </div>
          </div>

          {/* Test Results */}
          <div>
            {testResult ? (
              <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 14, padding: '1.25rem' }}>
                <h3 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 700, color: '#0F172A' }}>Test Results</h3>

                {/* Quality Score */}
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '0.75rem', background: '#F8FAFC', borderRadius: 10, marginBottom: 12
                }}>
                  <div>
                    <div style={{ fontSize: 11, color: '#64748B', fontWeight: 600 }}>QUALITY SCORE</div>
                    <div style={{ fontSize: 24, fontWeight: 800, color: '#0F172A' }}>
                      {((testResult.schemaValidation?.quality_score || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: '#64748B', fontWeight: 600 }}>COMPLETENESS</div>
                    <div style={{ fontSize: 24, fontWeight: 800, color: '#0F172A' }}>
                      {testResult.schemaValidation?.completeness_pct || 0}%
                    </div>
                  </div>
                  <div>
                    {testResult.schemaValidation?.hitl_required ?
                      <Badge color="#EF4444">HITL Required</Badge> :
                      <Badge color="#10B981">Auto-Complete</Badge>
                    }
                  </div>
                </div>

                {/* Extracted Fields */}
                <h4 style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 700, color: '#0F172A' }}>Extracted Fields</h4>
                <div style={{ maxHeight: 200, overflowY: 'auto', marginBottom: 12 }}>
                  {Object.entries(testResult.extractedFields || {}).map(([key, val]) => (
                    <div key={key} style={{
                      display: 'flex', justifyContent: 'space-between', padding: '5px 8px',
                      borderBottom: '1px solid #F1F5F9', fontSize: 12
                    }}>
                      <span style={{ fontWeight: 600, color: '#475569', fontFamily: 'monospace' }}>{key}</span>
                      <span style={{ color: val ? '#0F172A' : '#94A3B8', maxWidth: '60%', textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {val !== null && val !== undefined ? String(val) : '—'}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Field outcomes */}
                {testResult.schemaValidation?.field_outcomes?.length > 0 && (
                  <>
                    <h4 style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 700, color: '#0F172A' }}>Field Validation</h4>
                    <div style={{ maxHeight: 150, overflowY: 'auto' }}>
                      {testResult.schemaValidation.field_outcomes.map((fo: any, i: number) => (
                        <div key={i} style={{
                          display: 'flex', alignItems: 'center', gap: 8, padding: '4px 8px',
                          borderBottom: '1px solid #F1F5F9', fontSize: 12
                        }}>
                          {fo.passed ? <CheckCircle size={12} color="#10B981" /> : <XCircle size={12} color="#EF4444" />}
                          <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#475569' }}>{fo.field_key}</span>
                          {fo.error && <span style={{ color: '#EF4444', fontSize: 11 }}>{fo.error}</span>}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div style={{
                background: '#FFFFFF', border: '2px dashed #E2E8F0', borderRadius: 14, padding: '3rem',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#94A3B8'
              }}>
                <Play size={32} style={{ marginBottom: 12, opacity: 0.3 }} />
                <p style={{ margin: 0, fontSize: 13 }}>Run a test to see results here</p>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default SchemaBuilder;
