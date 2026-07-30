import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

import { Dashboard } from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { Processing } from './pages/Processing';
import { Results } from './pages/Results';
import { InvoiceProcessing } from './pages/InvoiceProcessing';
import { BatchProcessing } from './pages/BatchProcessing';
import { Settings } from './pages/Settings';

import type { SystemKPIs, WorkerNode, UniversalDocumentDataset, LogEntry } from './types';
import { getApiUrl, getWsUrl } from './config/api';

const emptyKPIs: SystemKPIs = {
  totalDocuments: 0,
  processedDocuments: 0,
  pendingDocuments: 0,
  successRate: 0.0
};

const emptyDataset: UniversalDocumentDataset = {
  schema: [],
  rows: []
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('upload');
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [kpis, setKpis] = useState<SystemKPIs>(emptyKPIs);
  const [workers, setWorkers] = useState<WorkerNode[]>([]);
  const [dataset, setDataset] = useState<UniversalDocumentDataset>(emptyDataset);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const fetchDataset = async () => {
    try {
      const resRows = await fetch(getApiUrl('/api/excel-rows'));
      if (resRows.ok) {
        const data = await resRows.json();
        if (data.schema && data.rows) {
          setDataset(data);
        } else if (Array.isArray(data)) {
          setDataset({ schema: [], rows: data });
        }
      }
    } catch (e) {}
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const resStatus = await fetch(getApiUrl('/api/status'));
        if (resStatus.ok) {
          const data = await resStatus.json();
          if (data.kpis) setKpis(data.kpis);
          if (data.queue && data.queue.workers) setWorkers(data.queue.workers);
        }

        await fetchDataset();

        const resLogs = await fetch(getApiUrl('/api/logs'));
        if (resLogs.ok) {
          const lData = await resLogs.json();
          setLogs(lData);
        }
      } catch (e) {}
    };

    fetchData();

    // Setup WebSocket
    const wsUrl = getWsUrl();
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
            if (payload.excelData) setDataset(payload.excelData);
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
        jobsCount={dataset.rows.length}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          wsConnected={wsConnected}
          onRefresh={fetchDataset}
          title="Universal AI Document Intelligence Platform"
          subtitle="Dynamic Schema Discovery & Extraction Engine"
        />

        <main className="flex-1 overflow-y-auto pb-12">
          {activeTab === 'dashboard' && (
            <Dashboard 
              kpis={kpis} 
              dataset={dataset} 
              onNavigate={setActiveTab} 
            />
          )}
          {activeTab === 'upload' && <Upload onNavigate={setActiveTab} />}
          {activeTab === 'inspector' && <InvoiceProcessing />}
          {activeTab === 'batch' && (
            <BatchProcessing 
              kpis={kpis} 
              workers={workers} 
              onNavigate={setActiveTab} 
            />
          )}
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
              dataset={dataset} 
              onRefresh={fetchDataset} 
            />
          )}
          {activeTab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
};

export default App;
