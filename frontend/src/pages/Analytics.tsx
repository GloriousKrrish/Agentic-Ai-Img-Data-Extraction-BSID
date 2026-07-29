import React from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { TrendingUp } from 'lucide-react';

const throughputData = [
  { hour: '08:00', invoices: 15 },
  { hour: '10:00', invoices: 42 },
  { hour: '12:00', invoices: 88 },
  { hour: '14:00', invoices: 130 },
  { hour: '16:00', invoices: 195 },
  { hour: '18:00', invoices: 240 },
];

const modelUsageData = [
  { name: 'Gemini 3.5 Flash', value: 85, color: '#E60012' },
  { name: 'Gemini 2.5 Flash', value: 12, color: '#005BAC' },
  { name: 'Gemini 2.5 Lite', value: 3, color: '#10B981' },
];

const confidenceDistData = [
  { range: '95-100%', count: 180 },
  { range: '90-95%', count: 45 },
  { range: '85-90%', count: 12 },
  { range: '<85%', count: 3 },
];

export const Analytics: React.FC = () => {
  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h2 className="text-2xl font-extrabold text-[#1B1B1B] tracking-tight">Enterprise Analytics & Metrics</h2>
        <p className="text-xs text-[#6B7280]">Performance analytics for Gemini AI models, extraction confidence, and worker utilization</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Hourly Extraction Volume Chart */}
        <div className="glass-card rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-extrabold text-[#1E293B] text-sm">Hourly Extraction Volume</h3>
            <span className="text-xs text-emerald-600 font-bold flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" /> +24% vs yesterday
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={throughputData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="hour" stroke="#94A3B8" fontSize={11} />
                <YAxis stroke="#94A3B8" fontSize={11} />
                <Tooltip contentStyle={{ borderRadius: '12px', borderColor: '#ECECEC' }} />
                <Area type="monotone" dataKey="invoices" stroke="#005BAC" fill="#005BAC20" strokeWidth={3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model Quota & Rotation Distribution */}
        <div className="glass-card rounded-2xl p-6 space-y-4">
          <h3 className="font-extrabold text-[#1E293B] text-sm">Gemini Model Utilization & Fallbacks</h3>
          
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie 
                  data={modelUsageData} 
                  cx="50%" 
                  cy="50%" 
                  innerRadius={60} 
                  outerRadius={90} 
                  paddingAngle={4}
                  dataKey="value"
                >
                  {modelUsageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="flex justify-center gap-6 text-xs font-semibold">
            {modelUsageData.map(m => (
              <div key={m.name} className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: m.color }}></span>
                <span className="text-[#1E293B]">{m.name} ({m.value}%)</span>
              </div>
            ))}
          </div>
        </div>

        {/* Confidence Score Distribution */}
        <div className="glass-card rounded-2xl p-6 space-y-4 lg:col-span-2">
          <h3 className="font-extrabold text-[#1E293B] text-sm">Confidence Score Distribution</h3>
          
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={confidenceDistData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="range" stroke="#94A3B8" fontSize={11} />
                <YAxis stroke="#94A3B8" fontSize={11} />
                <Tooltip contentStyle={{ borderRadius: '12px', borderColor: '#ECECEC' }} />
                <Bar dataKey="count" fill="#E60012" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
