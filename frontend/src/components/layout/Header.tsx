import React from 'react';
import { RefreshCw } from 'lucide-react';

interface HeaderProps {
  wsConnected: boolean;
  onRefresh?: () => void;
  title?: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ 
  wsConnected, 
  onRefresh, 
  title = "Agentic AI Data Extraction Platform", 
  subtitle = "Multimodal Document Intelligence & Dynamic Schema Engine" 
}) => {
  return (
    <header style={{
      height: 64,
      background: '#FFFFFF',
      borderBottom: '1px solid #E2E8F0',
      padding: '0 2rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 20,
      boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)'
    }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <h1 style={{ fontSize: 16, fontWeight: 800, color: '#0F172A', margin: 0, letterSpacing: '-0.02em' }}>
            {title}
          </h1>
          <span className="badge badge-neutral" style={{ fontSize: 10, fontWeight: 700 }}>
            ENTERPRISE EDITION
          </span>
        </div>
        <p style={{ fontSize: 12, color: '#64748B', margin: 0, fontWeight: 500, marginTop: 1 }}>{subtitle}</p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        {/* Status Indicator */}
        <div className={wsConnected ? 'badge badge-success' : 'badge badge-warning'} style={{ padding: '5px 12px', gap: 6 }}>
          <span style={{
            width: 7, height: 7, borderRadius: 9999,
            background: wsConnected ? '#10B981' : '#F59E0B',
          }} />
          <span>{wsConnected ? 'Live Socket Sync' : 'Live Sync (HTTP)'}</span>
        </div>

        {/* Refresh Button */}
        {onRefresh && (
          <button 
            onClick={onRefresh} 
            className="btn-secondary"
            style={{ padding: '6px 10px', borderRadius: 8 }}
            title="Refresh Pipeline Data"
          >
            <RefreshCw size={14} />
          </button>
        )}

        {/* Profile Pill */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          paddingLeft: 14, borderLeft: '1px solid #E2E8F0',
        }}>
          <div style={{
            width: 34, height: 34, borderRadius: 8,
            background: '#4F46E5',
            color: 'white', fontWeight: 800, fontSize: 12,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 1px 2px rgba(79, 70, 229, 0.2)',
          }}>
            AI
          </div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#0F172A' }}>Agentic AI Admin</div>
            <div style={{ fontSize: 11, color: '#64748B', fontWeight: 500 }}>System Controller</div>
          </div>
        </div>
      </div>
    </header>
  );
};
