// Centralized API and WebSocket URL helper for deployment flexibility

export const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string') {
    return envUrl.replace(/\/$/, '');
  }
  return ''; // Relative path (works for Vercel serverless /api route or Vite proxy)
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
