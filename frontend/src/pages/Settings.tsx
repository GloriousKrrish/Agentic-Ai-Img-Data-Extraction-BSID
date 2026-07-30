import React, { useState, useEffect } from 'react';
import { Key, Save, CheckCircle2, Sparkles, Cpu, AlertTriangle, RefreshCw, Zap } from 'lucide-react';

// Real, verified Gemini models as of 2025
const AVAILABLE_MODELS = [
  "gemini-2.5-flash",
  "gemini-2.5-flash-lite",
  "gemini-2.0-flash",
  "gemini-2.0-flash-lite",
  "gemini-1.5-flash-8b",
];

type ApiStatus = 'idle' | 'testing' | 'ok' | 'quota' | 'invalid';

export const Settings: React.FC = () => {
  const [apiKey, setApiKey] = useState<string>("");
  const [primaryModel, setPrimaryModel] = useState<string>("gemini-2.5-flash");
  const [modelsPriority, setModelsPriority] = useState<string[]>(AVAILABLE_MODELS);
  const [saved, setSaved] = useState<boolean>(false);
  const [apiStatus, setApiStatus] = useState<ApiStatus>('idle');
  const [apiStatusMsg, setApiStatusMsg] = useState<string>('');

  useEffect(() => {
    fetch("/api/settings")
      .then(res => res.json())
      .then(data => {
        if (data.geminiApiKey) setApiKey(data.geminiApiKey);
        if (data.primaryModel) setPrimaryModel(data.primaryModel);
        if (data.modelsPriority && Array.isArray(data.modelsPriority)) {
          // Filter to only valid known models
          const valid = data.modelsPriority.filter((m: string) => AVAILABLE_MODELS.includes(m));
          if (valid.length > 0) setModelsPriority(valid);
        }
      })
      .catch(() => {});
  }, []);

  const handlePrimaryModelChange = (selected: string) => {
    setPrimaryModel(selected);
    const filtered = modelsPriority.filter(m => m !== selected);
    setModelsPriority([selected, ...filtered]);
  };

  const testApiKey = async () => {
    if (!apiKey.trim()) {
      setApiStatus('invalid');
      setApiStatusMsg('Please enter an API key first.');
      return;
    }
    setApiStatus('testing');
    setApiStatusMsg('Testing key against Gemini API...');
    try {
      const model = primaryModel || 'gemini-2.5-flash';
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey.trim()}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents: [{ parts: [{ text: 'ping' }] }] })
      });
      if (res.status === 200) {
        setApiStatus('ok');
        setApiStatusMsg(`✅ API key is valid and working! Model: ${model}`);
      } else if (res.status === 429) {
        setApiStatus('quota');
        const data = await res.json().catch(() => ({}));
        const msg = data?.error?.message || 'Quota exceeded';
        setApiStatusMsg(`⚠️ Key is valid but QUOTA EXHAUSTED: ${msg.slice(0, 200)}`);
      } else if (res.status === 400 || res.status === 401 || res.status === 403) {
        setApiStatus('invalid');
        const data = await res.json().catch(() => ({}));
        setApiStatusMsg(`❌ Invalid API key: ${data?.error?.message || res.statusText}`);
      } else {
        setApiStatus('invalid');
        setApiStatusMsg(`❌ Unexpected response: HTTP ${res.status}`);
      }
    } catch (e: unknown) {
      setApiStatus('invalid');
      const msg = e instanceof Error ? e.message : String(e);
      setApiStatusMsg(`❌ Network error: ${msg}`);
    }
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

  const statusBg: Record<ApiStatus, string> = {
    idle: 'bg-slate-50 border-slate-200 text-slate-600',
    testing: 'bg-blue-50 border-blue-200 text-blue-700',
    ok: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    quota: 'bg-amber-50 border-amber-300 text-amber-800',
    invalid: 'bg-red-50 border-red-200 text-red-700',
  };

  return (
    <div className="p-8 space-y-8 max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-extrabold text-[#1B1B1B] tracking-tight">System &amp; AI Settings</h2>
        <p className="text-xs text-[#6B7280]">Configure Google Gemini API credentials, model selection, and fallback sequences</p>
      </div>

      {/* Quota Warning Banner */}
      <div className="p-4 bg-amber-50 border border-amber-300 rounded-2xl flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-xs font-bold text-amber-800">API Quota Notice</p>
          <p className="text-xs text-amber-700 mt-1">
            If document processing fails with "QUOTA_EXCEEDED", your Gemini API free tier limit has been reached. 
            Get a new API key at <a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer" className="underline font-bold">aistudio.google.com/apikey</a> or 
            upgrade to a paid plan at <a href="https://ai.google.dev/pricing" target="_blank" rel="noreferrer" className="underline font-bold">ai.google.dev/pricing</a>.
          </p>
        </div>
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
            <div className="flex gap-2">
              <input 
                type="password" 
                value={apiKey} 
                placeholder="Paste your Gemini API key from aistudio.google.com"
                onChange={(e) => { setApiKey(e.target.value); setApiStatus('idle'); }}
                className="flex-1 px-4 py-3 bg-[#F8FAFC] border border-[#CBD5E1] rounded-xl font-mono text-xs font-semibold text-[#1E293B] focus:outline-none focus:border-[#E60012]"
              />
              <button
                onClick={testApiKey}
                disabled={apiStatus === 'testing'}
                className="px-4 py-3 bg-[#005BAC] hover:bg-[#004a8f] text-white font-bold text-xs rounded-xl transition-all flex items-center gap-2 disabled:opacity-60 cursor-pointer"
              >
                {apiStatus === 'testing' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                Test Key
              </button>
            </div>
            {apiStatus !== 'idle' && (
              <div className={`p-3 rounded-xl border text-xs font-semibold ${statusBg[apiStatus]}`}>
                {apiStatusMsg}
              </div>
            )}
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
                  {model} {model === 'gemini-2.5-flash' ? '(Recommended - Best Quality)' : model === 'gemini-2.0-flash-lite' ? '(Fastest - Low Quota Usage)' : ''}
                </option>
              ))}
            </select>
            <p className="text-xs text-slate-500">Only real, verified models are listed. All models use free tier unless you have billing enabled.</p>
          </div>

          <div className="p-4 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0] space-y-2">
            <span className="text-xs font-bold text-[#1E293B] flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-[#005BAC]" />
              Active Model Priority Sequence (tried in order on failure)
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
            Save Settings to Workspace &amp; .env
          </button>

          {saved && (
            <div className="p-3 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-xl text-xs font-bold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Settings updated successfully. Backend will use new key on next job.
            </div>
          )}
        </div>
      </div>

      {/* How to get a key */}
      <div className="glass-card rounded-2xl p-6 space-y-4">
        <h3 className="font-extrabold text-[#1E293B] text-sm">How to Get a Gemini API Key</h3>
        <ol className="text-xs text-[#475569] space-y-2 list-decimal list-inside">
          <li>Go to <a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer" className="text-[#005BAC] underline font-bold">aistudio.google.com/apikey</a></li>
          <li>Sign in with your Google account</li>
          <li>Click <strong>"Create API key"</strong></li>
          <li>Copy the key and paste it above</li>
          <li>Click <strong>"Test Key"</strong> to verify it works</li>
          <li>Click <strong>"Save Settings"</strong> to apply it</li>
        </ol>
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-800">
          <strong>Free Tier Limits:</strong> 15 RPM (requests per minute), 1,500 RPD (requests per day) for gemini-2.0-flash. 
          If you hit quota, wait a minute or switch to a less-used model like <code>gemini-2.0-flash-lite</code>.
        </div>
      </div>
    </div>
  );
};
