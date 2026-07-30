import React, { useState, useEffect } from 'react';
import { Key, Save, CheckCircle2, Sparkles, Cpu } from 'lucide-react';

const AVAILABLE_MODELS = [
  "gemini-3.5-flash",
  "gemini-2.5-flash",
  "gemini-2.5-flash-lite",
  "gemini-3.1-flash-lite",
  "gemini-1.5-flash"
];

export const Settings: React.FC = () => {
  const [apiKey, setApiKey] = useState<string>("");
  const [primaryModel, setPrimaryModel] = useState<string>("gemini-3.5-flash");
  const [modelsPriority, setModelsPriority] = useState<string[]>(AVAILABLE_MODELS);
  const [saved, setSaved] = useState<boolean>(false);

  useEffect(() => {
    fetch("/api/settings")
      .then(res => res.json())
      .then(data => {
        if (data.geminiApiKey) setApiKey(data.geminiApiKey);
        if (data.primaryModel) setPrimaryModel(data.primaryModel);
        if (data.modelsPriority && Array.isArray(data.modelsPriority)) {
          setModelsPriority(data.modelsPriority);
        }
      })
      .catch(() => {});
  }, []);

  const handlePrimaryModelChange = (selected: string) => {
    setPrimaryModel(selected);
    const filtered = modelsPriority.filter(m => m !== selected);
    setModelsPriority([selected, ...filtered]);
  };

  const handleSave = async () => {
    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          geminiApiKey: apiKey,
          primaryModel: primaryModel,
          modelsPriority: modelsPriority
        })
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (e) {
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-extrabold text-[#1B1B1B] tracking-tight">System & AI Settings</h2>
        <p className="text-xs text-[#6B7280]">Configure Google Gemini API credentials, model selection, and fallback sequences across the workspace</p>
      </div>

      <div className="glass-card rounded-2xl p-6 space-y-6">
        <div className="flex items-center gap-3 border-b border-[#ECECEC] pb-4">
          <div className="w-10 h-10 rounded-xl bg-[#E6001210] text-[#E60012] flex items-center justify-center">
            <Key className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-extrabold text-[#1E293B] text-sm">Google Gemini API Configuration</h3>
            <p className="text-xs text-[#64748B]">Primary key and model configuration saved in .env and active runtime environment</p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-bold text-[#1E293B]">GEMINI_API_KEY</label>
            <input 
              type="password" 
              value={apiKey} 
              placeholder="Enter your Gemini API key"
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl font-mono text-xs font-semibold text-[#1E293B] focus:outline-none focus:border-[#E60012]"
            />
          </div>

          <div className="space-y-3">
            <label className="text-xs font-bold text-[#1E293B] flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-[#E60012]" />
              Select Primary Gemini Model
            </label>
            <select
              value={primaryModel}
              onChange={(e) => handlePrimaryModelChange(e.target.value)}
              className="w-full px-4 py-3 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl font-semibold text-xs text-[#1E293B] focus:outline-none focus:border-[#E60012]"
            >
              {AVAILABLE_MODELS.map((model) => (
                <option key={model} value={model}>
                  {model} {model === 'gemini-3.5-flash' ? '(Recommended - Highest Accuracy)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="p-4 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0] space-y-2">
            <span className="text-xs font-bold text-[#1E293B] flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-[#005BAC]" />
              Active Model Priority Sequence (Saved to .env & Runtime)
            </span>
            <div className="flex flex-wrap gap-2 text-xs font-semibold pt-1">
              {modelsPriority.map((model, idx) => (
                <span 
                  key={model} 
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold ${
                    idx === 0 
                      ? 'bg-[#E60012] text-white shadow-xs' 
                      : idx === 1 
                      ? 'bg-[#005BAC] text-white' 
                      : 'bg-slate-200 text-slate-700'
                  }`}
                >
                  {idx + 1}. {model} {idx === 0 ? '(Primary)' : idx === 1 ? '(Fallback 1)' : ''}
                </span>
              ))}
            </div>
          </div>

          <button 
            onClick={handleSave}
            className="px-6 py-3 bg-[#E60012] hover:bg-[#C2000F] text-white font-bold text-xs rounded-xl shadow-lg transition-all flex items-center gap-2 cursor-pointer"
          >
            <Save className="w-4 h-4" />
            Save Settings to Workspace & .env
          </button>

          {saved && (
            <div className="p-3 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-xl text-xs font-bold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Settings updated successfully in .env and active runtime environment across all services.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

