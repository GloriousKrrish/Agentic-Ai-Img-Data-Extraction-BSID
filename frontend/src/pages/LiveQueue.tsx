import React from 'react';
import { motion } from 'framer-motion';
import { Cpu, Activity, Clock, ShieldCheck } from 'lucide-react';
import type { WorkerNode } from '../types';

interface LiveQueueProps {
  workers: WorkerNode[];
  pendingTasks: number;
  activeLocks: number;
}

export const LiveQueue: React.FC<LiveQueueProps> = ({ workers, pendingTasks, activeLocks }) => {
  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-[#1B1B1B] tracking-tight">Live Worker Node Monitoring</h2>
          <p className="text-xs text-[#6B7280]">Real-time thread state, active locks, and Gemini model rotation telemetry</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 bg-emerald-50 text-emerald-700 font-bold text-xs rounded-full border border-emerald-200 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" />
            {activeLocks} Active Locks
          </div>
          <div className="px-3 py-1.5 bg-slate-100 text-slate-700 font-bold text-xs rounded-full border border-slate-200 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            {pendingTasks} Pending Tasks
          </div>
        </div>
      </div>

      {/* Worker Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {workers.map((worker) => (
          <motion.div 
            key={worker.id}
            whileHover={{ y: -4 }}
            className="glass-card rounded-2xl p-6 space-y-5 relative overflow-hidden"
          >
            <div className="flex items-center justify-between border-b border-[#ECECEC] pb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-xl bg-[#005BAC10] text-[#005BAC] flex items-center justify-center font-bold">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-[#1E293B] text-sm">{worker.name}</h3>
                  <span className="text-[10px] text-[#64748B] font-semibold">ID: worker_{worker.id}</span>
                </div>
              </div>

              <span className={`px-3 py-1 rounded-full text-xs font-extrabold ${
                worker.status === 'RUNNING' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-700'
              }`}>
                {worker.status}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center p-2 bg-[#F8FAFC] rounded-lg">
                <span className="text-[#64748B] font-medium">Active Model</span>
                <span className="font-extrabold text-[#E60012] bg-[#E6001210] px-2 py-0.5 rounded">
                  {worker.modelUsed}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[#64748B] font-medium">Claimed Task</span>
                <span className="font-bold text-[#1E293B]">{worker.currentTask}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[#64748B] font-medium">Current Stage</span>
                <span className="font-semibold text-[#005BAC]">{worker.stage}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[#64748B] font-medium">Elapsed Time</span>
                <span className="font-bold text-slate-700">{worker.elapsed}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-[#64748B] font-medium">Confidence Score</span>
                <span className="font-bold text-emerald-600 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  {worker.confidence}%
                </span>
              </div>
            </div>

            {/* Last Log Line */}
            <div className="p-3 bg-slate-900 text-slate-200 rounded-xl font-mono text-[10px] truncate">
              {worker.lastLog || `Worker ${worker.id} standing by for next task...`}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
