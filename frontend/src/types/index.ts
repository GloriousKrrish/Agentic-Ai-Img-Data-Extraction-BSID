export interface DynamicColumnSchema {
  key: string;
  label: string;
  type?: string;
}

export interface DynamicDataRow {
  rowIndex: number;
  fields: Record<string, any>;
  status: 'COMPLETED' | 'PENDING' | 'PROCESSING' | 'FAILED';
  confidence?: number;
}

export interface UniversalDocumentDataset {
  schema: DynamicColumnSchema[];
  rows: DynamicDataRow[];
}

export type UniversalDataset = UniversalDocumentDataset;

export interface UniversalExtractedDocument {
  fileName?: string;
  fileType?: string;
  modelUsed?: string;
  category?: string;
  documentTitle?: string;
  extractedFields: Record<string, any>;
  schemaFields?: DynamicColumnSchema[];
  confidence: number;
  status: string;
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
