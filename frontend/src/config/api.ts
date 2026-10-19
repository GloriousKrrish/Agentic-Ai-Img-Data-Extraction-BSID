// Centralized API and WebSocket URL helper for deployment flexibility
const DEFAULT_PROD_API_URL = 'https://agentic-ai-img-data-extraction-bsid.onrender.com';

export const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim()) {
    return envUrl.replace(/\/$/, '');
  }
  // In production builds (Vercel), default to the live Render backend
  if (import.meta.env.PROD) {
    return DEFAULT_PROD_API_URL;
  }
  return ''; // Relative path for Vite dev proxy
};

export const getApiUrl = (endpoint: string): string => {
  const base = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return base ? `${base}${cleanEndpoint}` : cleanEndpoint;
};

export const getWsUrl = (): string => {
  const envWsUrl = import.meta.env.VITE_WS_URL;
  if (envWsUrl && typeof envWsUrl === 'string') {
    return envWsUrl;
  }
  
  const base = getApiBaseUrl();
  if (base.startsWith('http://') || base.startsWith('https://')) {
    const wsProtocol = base.startsWith('https://') ? 'wss://' : 'ws://';
    const host = base.replace(/^https?:\/\//, '');
    return `${wsProtocol}${host}/ws`;
  }

  const isHttps = window.location.protocol === 'https:';
  const wsProtocol = isHttps ? 'wss://' : 'ws://';
  return `${wsProtocol}${window.location.host}/ws`;
};
