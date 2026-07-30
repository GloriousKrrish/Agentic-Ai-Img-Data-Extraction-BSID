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

import type { SystemKPIs, WorkerNode, JobRecord, LogEntry } from './types';

const emptyKPIs: SystemKPIs = {
  totalDocuments: 0,
  processedDocuments: 0,
  pendingDocuments: 0,
  successRate: 0.0
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('upload');
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [kpis, setKpis] = useState<SystemKPIs>(emptyKPIs);
  const [workers, setWorkers] = useState<WorkerNode[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // 100% Backend-Owned Job State
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(() => {
    return localStorage.getItem('current_active_job_id') || null;
  });

  const fetchJobs = async () => {
    try {
      const res = await fetch('/api/jobs');
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (e) {}
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      const res = await fetch(`/api/jobs/${jobId}`, { method: 'DELETE' });
      if (res.ok) {
        await fetchJobs();
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

        await fetchJobs();

        const resLogs = await fetch('/api/logs');
        if (resLogs.ok) {
          const lData = await resLogs.json();
          setLogs(lData);
        }
      } catch (e) {}
    };

    fetchData();

    // HTTP polling every 2s for live job updates
    const pollInterval = setInterval(() => {
      fetchJobs();
    }, 2000);

    // Setup WebSocket for real-time sync
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
            if (payload.jobs) setJobs(payload.jobs);
            if (payload.logs) setLogs(payload.logs);
          }
        } catch (err) {}
      };
    } catch (err) {
      setWsConnected(false);
    }

    return () => {
      clearInterval(pollInterval);
      if (socket) socket.close();
    };
  }, []);

  const activeJob = jobs.find(j => j.job_id === activeJobId) || (jobs.length > 0 ? jobs[0] : null);
  const activeSchema = activeJob?.schema || [];
  const activeRows = activeJob?.rows || [];

  return (
    <div className="min-h-screen bg-[#FCFCFC] flex text-slate-900 font-sans">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        pendingCount={kpis.pendingDocuments}
        jobsCount={jobs.filter(j => j.status === 'Completed').length}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          wsConnected={wsConnected}
          onRefresh={fetchJobs}
          title="Universal AI Document Intelligence Platform"
          subtitle="Enterprise Backend-Owned Persistent Job Manager"
        />

        <main className="flex-1 overflow-y-auto pb-12">
          {activeTab === 'dashboard' && (
            <Dashboard
              kpis={kpis}
              schema={activeSchema}
              recentRows={activeRows}
              onNavigate={setActiveTab}
            />
          )}
          {activeTab === 'upload' && (
            <Upload onNavigate={setActiveTab} />
          )}
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
              jobs={jobs}
              activeJobId={activeJobId}
              onSelectJob={(id) => {
                setActiveJobId(id);
                localStorage.setItem('current_active_job_id', id);
              }}
              onDeleteJob={handleDeleteJob}
              onRefresh={fetchJobs}
            />
          )}
          {activeTab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
};

export default App;
