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

  // Persistent Job State Management across navigation & refresh
  const [currentJobId, setCurrentJobId] = useState<string>(() => {
    return localStorage.getItem('current_active_job_id') || '';
  });
  const [activeJob, setActiveJob] = useState<any | null>(null);
  const [allJobs, setAllJobs] = useState<any[]>([]);

  const handleJobCreated = (jobId: string) => {
    setCurrentJobId(jobId);
    localStorage.setItem('current_active_job_id', jobId);
  };

  const fetchJobState = async () => {
    try {
      // 1. Fetch All User Jobs
      const resJobs = await fetch(getApiUrl('/api/jobs'));
      if (resJobs.ok) {
        const jobsList = await resJobs.json();
        setAllJobs(jobsList);

        if (!currentJobId && jobsList.length > 0) {
          const latestId = jobsList[0].job_id;
          setCurrentJobId(latestId);
          localStorage.setItem('current_active_job_id', latestId);
        }
      }

      // 2. Fetch Active Job Details if ID is present
      const jobIdToFetch = currentJobId || localStorage.getItem('current_active_job_id');
      if (jobIdToFetch) {
        const resSingleJob = await fetch(getApiUrl(`/api/jobs/${jobIdToFetch}`));
        if (resSingleJob.ok) {
          const singleJob = await resSingleJob.json();
          setActiveJob(singleJob);

          if (singleJob.schema && singleJob.rows) {
            setDataset({
              schema: singleJob.schema,
              rows: singleJob.rows
            });
          }
          if (singleJob.logs && Array.isArray(singleJob.logs)) {
            setLogs(singleJob.logs);
          }
        }
      }

      // 3. Fetch KPI & Status Summary
      const resStatus = await fetch(getApiUrl('/api/status'));
      if (resStatus.ok) {
        const data = await resStatus.json();
        if (data.kpis) setKpis(data.kpis);
        if (data.queue && data.queue.workers) setWorkers(data.queue.workers);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchJobState();

    // 1000ms polling loop for state recovery & live progress synchronization
    const interval = setInterval(fetchJobState, 1000);

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
            if (payload.excelData && payload.excelData.schema && payload.excelData.schema.length > 0) {
              setDataset(payload.excelData);
            }
          }
        } catch (err) {}
      };
    } catch (err) {
      setWsConnected(false);
    }

    return () => {
      clearInterval(interval);
      if (socket) socket.close();
    };
  }, [currentJobId]);

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
          onRefresh={fetchJobState}
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
          {activeTab === 'upload' && (
            <Upload 
              onNavigate={setActiveTab} 
              onJobCreated={handleJobCreated}
            />
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
              activeJob={activeJob}
              onNavigate={setActiveTab}
            />
          )}
          {activeTab === 'results' && (
            <Results 
              dataset={dataset} 
              onRefresh={fetchJobState}
              activeJob={activeJob}
              allJobs={allJobs}
              onSelectJob={async (id) => {
                setCurrentJobId(id);
                localStorage.setItem('current_active_job_id', id);
                try {
                  const res = await fetch(getApiUrl(`/api/jobs/${id}`));
                  if (res.ok) {
                    const singleJob = await res.json();
                    setActiveJob(singleJob);
                    if (singleJob.schema && singleJob.rows) {
                      setDataset({
                        schema: singleJob.schema,
                        rows: singleJob.rows
                      });
                    }
                  }
                } catch (e) {}
              }}
            />
          )}
          {activeTab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
};

export default App;
