import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

import { Dashboard } from './pages/Dashboard';
import { InvoiceProcessing } from './pages/InvoiceProcessing';
import { BatchProcessing } from './pages/BatchProcessing';
import { LiveQueue } from './pages/LiveQueue';
import { LiveExcelSync } from './pages/LiveExcelSync';
import { Results } from './pages/Results';
import { AILogs } from './pages/AILogs';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';

import type { SystemKPIs, WorkerNode, InvoiceRow, LogEntry } from './types';
import { motion, AnimatePresence } from 'framer-motion';

const defaultKPIs: SystemKPIs = {
  totalInvoices: 247,
  processedInvoices: 182,
  pendingInvoices: 65,
  successRate: 98.4,
  avgConfidence: 98.6,
  avgProcessingTime: "2.4s",
  geminiRequests: 378
};

const defaultWorkers: WorkerNode[] = [
  {
    id: 1,
    name: 'Worker Node 1',
    status: 'RUNNING',
    currentTask: 'Row #14',
    stage: 'Gemini Multimodal Extraction',
    modelUsed: 'gemini-3.5-flash',
    elapsed: '3.8s',
    speed: '1.4 img/s',
    retries: 0,
    confidence: 99.1,
    lastLog: 'Worker 1 - Claimed Row 14. Querying Gemini API...'
  },
  {
    id: 2,
    name: 'Worker Node 2',
    status: 'RUNNING',
    currentTask: 'Row #15',
    stage: 'JSON Validation & Sanitization',
    modelUsed: 'gemini-3.5-flash',
    elapsed: '2.1s',
    speed: '1.2 img/s',
    retries: 0,
    confidence: 98.2,
    lastLog: 'Worker 2 - Cleaned vehicle plate AP05EY5775'
  },
  {
    id: 3,
    name: 'Worker Node 3',
    status: 'READY',
    currentTask: 'Idle',
    stage: 'Awaiting Queue',
    modelUsed: 'gemini-2.5-flash (Standby)',
    elapsed: '0s',
    speed: '0 img/s',
    retries: 0,
    confidence: 100.0,
    lastLog: 'Worker 3 - Standing by for task assignment'
  }
];

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [kpis, setKpis] = useState<SystemKPIs>(defaultKPIs);
  const [workers, setWorkers] = useState<WorkerNode[]>(defaultWorkers);
  const [excelRows, setExcelRows] = useState<InvoiceRow[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Initial Fetch & WebSocket Connection
  useEffect(() => {
    const fetchData = async () => {
      try {
        const resStatus = await fetch('/api/status');
        if (resStatus.ok) {
          const data = await resStatus.json();
          if (data.kpis) setKpis(data.kpis);
          if (data.queue && data.queue.workers) setWorkers(data.queue.workers);
        }

        const resRows = await fetch('/api/excel-rows');
        if (resRows.ok) {
          const rows = await resRows.json();
          setExcelRows(rows);
        }

        const resLogs = await fetch('/api/logs');
        if (resLogs.ok) {
          const lData = await resLogs.json();
          setLogs(lData);
        }
      } catch (e) {
        console.warn('Backend API connection offline, running in dynamic preview mode.');
      }
    };

    fetchData();

    // WebSocket Stream Setup
    const wsUrl = `ws://${window.location.host}/ws`;
    let socket: WebSocket;
    try {
      socket = new WebSocket(wsUrl);
      socket.onopen = () => setWsConnected(true);
      socket.onclose = () => setWsConnected(false);
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'SYNC_UPDATE') {
            if (payload.kpis) setKpis(payload.kpis);
            if (payload.queue && payload.queue.workers) setWorkers(payload.queue.workers);
            if (payload.recentRows && payload.recentRows.length > 0) setExcelRows(payload.recentRows);
            if (payload.logs) setLogs(payload.logs);
          }
        } catch (err) {}
      };
    } catch (err) {
      setWsConnected(false);
    }

    return () => {
      if (socket) socket.close();
    };
  }, []);

  const handleRefresh = async () => {
    try {
      const resRows = await fetch('/api/excel-rows');
      if (resRows.ok) setExcelRows(await resRows.json());
    } catch (e) {}
  };

  return (
    <div className="min-h-screen bg-[#FCFCFC] flex text-[#1B1B1B]">
      {/* Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        pendingCount={kpis.pendingInvoices}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          wsConnected={wsConnected}
          onRefresh={handleRefresh}
          title="Bridgestone Agentic AI Data Extraction Engine"
          subtitle="Enterprise Document Intelligence Platform"
        />

        <main className="flex-1 overflow-y-auto pb-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === 'dashboard' && (
                <Dashboard 
                  kpis={kpis} 
                  workers={workers} 
                  recentRows={excelRows} 
                  onNavigate={setActiveTab} 
                />
              )}
              {activeTab === 'invoice-processing' && <InvoiceProcessing />}
              {activeTab === 'batch-processing' && (
                <BatchProcessing 
                  kpis={kpis} 
                  workers={workers} 
                  onNavigate={setActiveTab} 
                />
              )}
              {activeTab === 'live-queue' && (
                <LiveQueue 
                  workers={workers} 
                  pendingTasks={kpis.pendingInvoices} 
                  activeLocks={0} 
                />
              )}
              {activeTab === 'excel-sync' && (
                <LiveExcelSync 
                  rows={excelRows} 
                  onRefresh={handleRefresh} 
                />
              )}
              {activeTab === 'results' && <Results rows={excelRows} />}
              {activeTab === 'ai-logs' && <AILogs logs={logs} />}
              {activeTab === 'analytics' && <Analytics />}
              {activeTab === 'settings' && <Settings />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

export default App;
