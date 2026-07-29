export interface InvoiceRow {
  rowIndex: number;
  url: string;
  customerName: string;
  customerMobile: string;
  vehicleNumber: string;
  size: string;
  pattern: string;
  dot: string;
  cost: string;
  totalCost: string;
  dealerName: string;
  status: 'COMPLETED' | 'PENDING' | 'PROCESSING' | 'FAILED';
  confidence: number;
}

export interface WorkerNode {
  id: number;
  name: string;
  status: 'RUNNING' | 'READY' | 'PAUSED' | 'ERROR';
  currentTask: string;
  stage: string;
  modelUsed: string;
  elapsed: string;
  speed: string;
  retries: number;
  confidence: number;
  lastLog: string;
}

export interface SystemKPIs {
  totalInvoices: number;
  processedInvoices: number;
  pendingInvoices: number;
  successRate: number;
  avgConfidence: number;
  avgProcessingTime: string;
  geminiRequests: number;
}

export interface LogEntry {
  timestamp: string;
  worker: string;
  message: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS';
}

export interface ExtractedInvoice {
  fileName?: string;
  modelUsed: string;
  customerName: string;
  customerMobile: string;
  vehicleNumber: string;
  size: string;
  pattern: string;
  dot: string;
  cost: string;
  totalCost: string;
  dealerName: string;
  confidence: number;
  status: string;
}
