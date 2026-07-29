import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

import { Dashboard } from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { Processing } from './pages/Processing';
import { Results } from './pages/Results';

import type { SystemKPIs, WorkerNode, InvoiceRow, LogEntry } from './types';

const emptyKPIs: SystemKPIs = {
  totalInvoices: 0,
  processedInvoices: 0,
  pendingInvoices: 0,
  successRate: 0.0
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [kpis, setKpis] = useState<SystemKPIs>(emptyKPIs);
  const [workers, setWorkers] = useState<WorkerNode[]>([]);
  const [excelRows, setExcelRows] = useState<InvoiceRow[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Fetch real data & connect WebSocket
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
            if (payload.recentRows) setExcelRows(payload.recentRows);
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
    <div className="min-h-screen bg-[#FCFCFC] flex text-slate-900 font-sans">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        pendingCount={kpis.pendingInvoices}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          wsConnected={wsConnected}
          onRefresh={handleRefresh}
          title="Bridgestone Agentic AI Data Extraction Engine"
          subtitle="Real-time Document Intelligence Platform"
        />

        <main className="flex-1 overflow-y-auto pb-12">
          {activeTab === 'dashboard' && (
            <Dashboard 
              kpis={kpis} 
              recentRows={excelRows} 
              onNavigate={setActiveTab} 
            />
          )}
          {activeTab === 'upload' && <Upload onNavigate={setActiveTab} />}
          {activeTab === 'processing' && (
            <Processing 
              workers={workers} 
              pendingTasks={kpis.pendingInvoices} 
              activeLocks={0}
              logs={logs}
            />
          )}
          {activeTab === 'results' && (
            <Results 
              rows={excelRows} 
              onRefresh={handleRefresh} 
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
