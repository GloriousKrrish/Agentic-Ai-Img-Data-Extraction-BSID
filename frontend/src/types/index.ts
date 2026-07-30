export interface SchemaColumn {
  key: string;
  label: string;
  type?: string;
}

export interface DynamicRow {
  rowIndex: number;
  fields: Record<string, any>;
  status: string;
  confidence?: number;
}

export interface UniversalDataset {
  schema: SchemaColumn[];
  rows: DynamicRow[];
  documentCategory?: string;
  documentTitle?: string;
  fileName?: string;
  fileType?: string;
  modelUsed?: string;
  confidence?: number;
  status?: string;
}

export interface WorkerNode {
  id: number;
  name: string;
  status: 'RUNNING' | 'READY' | 'PAUSED' | 'ERROR';
  currentTask: string;
  stage: string;
  modelUsed?: string;
  elapsed?: string;
  confidence?: number;
  lastLog: string;
}

export interface SystemKPIs {
  totalDocuments: number;
  processedDocuments: number;
  pendingDocuments: number;
  successRate: number;
}

export interface LogEntry {
  timestamp: string;
  worker: string;
  message: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS';
}
