import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

import { Dashboard } from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { Processing } from './pages/Processing';
import { Results } from './pages/Results';
import { InvoiceProcessing } from './pages/InvoiceProcessing';

import type { SystemKPIs, WorkerNode, SchemaColumn, DynamicRow, LogEntry } from './types';

const emptyKPIs: SystemKPIs = {
  totalDocuments: 0,
  processedDocuments: 0,
  pendingDocuments: 0,
  successRate: 0.0
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [kpis, setKpis] = useState<SystemKPIs>(emptyKPIs);
  const [workers, setWorkers] = useState<WorkerNode[]>([]);
  
  const [schema, setSchema] = useState<SchemaColumn[]>(() => {
    try {
      const saved = localStorage.getItem("active_schema");
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  });

  const [rows, setRows] = useState<DynamicRow[]>(() => {
    try {
      const saved = localStorage.getItem("active_rows");
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  });

  const [logs, setLogs] = useState<LogEntry[]>([]);

  const handleDatasetExtracted = (dataset: { schema: SchemaColumn[]; rows: DynamicRow[] }) => {
    if (dataset.schema && dataset.schema.length > 0) {
      setSchema(dataset.schema);
      try { localStorage.setItem("active_schema", JSON.stringify(dataset.schema)); } catch (e) {}
    }
    if (dataset.rows && dataset.rows.length > 0) {
      setRows(dataset.rows);
      try { localStorage.setItem("active_rows", JSON.stringify(dataset.rows)); } catch (e) {}
    }
  };

  const handleFetchExcelData = async () => {
    try {
      const resRows = await fetch('/api/excel-rows');
      if (resRows.ok) {
        const data = await resRows.json();
        if (data.schema && data.schema.length > 0) {
          setSchema(data.schema);
          try { localStorage.setItem("active_schema", JSON.stringify(data.schema)); } catch (e) {}
        }
        if (data.rows && data.rows.length > 0) {
          setRows(data.rows);
          try { localStorage.setItem("active_rows", JSON.stringify(data.rows)); } catch (e) {}
        }
      }
    } catch (e) {}
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const resStatus = await fetch('/api/status');
        if (resStatus.ok) {
          const data = await resStatus.json();
          if (data.kpis) setKpis(data.kpis);
          if (data.queue && data.queue.workers) setWorkers(data.queue.workers);
        }

        await handleFetchExcelData();

        const resLogs = await fetch('/api/logs');
        if (resLogs.ok) {
          const lData = await resLogs.json();
          setLogs(lData);
        }
      } catch (e) {}
    };

    fetchData();

    // Setup WebSocket
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
            if (payload.excelData) {
              if (payload.excelData.schema && payload.excelData.schema.length > 0) {
                setSchema(payload.excelData.schema);
              }
              if (payload.excelData.rows && payload.excelData.rows.length > 0) {
                setRows(payload.excelData.rows);
              }
            }
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

  return (
    <div className="min-h-screen bg-[#FCFCFC] flex text-slate-900 font-sans">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        pendingCount={kpis.pendingDocuments}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          wsConnected={wsConnected}
          onRefresh={handleFetchExcelData}
          title="Universal AI Document Intelligence Platform"
          subtitle="Real-time Dynamic AI Data Extraction Engine"
        />

        <main className="flex-1 overflow-y-auto pb-12">
          {activeTab === 'dashboard' && (
            <Dashboard 
              kpis={kpis} 
              schema={schema}
              recentRows={rows} 
              onNavigate={setActiveTab} 
            />
          )}
          {activeTab === 'upload' && (
            <Upload 
              onNavigate={setActiveTab} 
              onDatasetExtracted={handleDatasetExtracted}
            />
          )}
          {activeTab === 'inspector' && <InvoiceProcessing />}
          {activeTab === 'processing' && (
            <Processing 
              workers={workers} 
              pendingTasks={kpis.pendingDocuments} 
              activeLocks={0}
              logs={logs}
            />
          )}
          {activeTab === 'results' && (
            <Results 
              schema={schema}
              rows={rows} 
              onRefresh={handleFetchExcelData} 
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
