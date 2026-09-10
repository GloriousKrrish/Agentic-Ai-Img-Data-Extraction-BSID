import React from 'react';
import { 
  LayoutDashboard, 
  Upload, 
  Table, 
  ScanSearch, 
  Layers, 
  Settings, 
  Activity, 
  Bot,
  Sparkles
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingCount?: number;
  jobsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, pendingCount = 0, jobsCount = 0 }) => {
  const navItems = [
    { id: 'upload', label: 'Upload & Extract', icon: Upload, group: 'main' },
    { id: 'inspector', label: 'Document Inspector', icon: ScanSearch, group: 'main' },
    { id: 'batch', label: 'Batch Queue', icon: Layers, group: 'main', badge: pendingCount > 0 ? `${pendingCount}` : undefined },
    { id: 'results', label: 'Extracted Results', icon: Table, group: 'data', badge: jobsCount > 0 ? `${jobsCount}` : undefined },
    { id: 'processing', label: 'Job Telemetry', icon: Activity, group: 'data' },
    { id: 'dashboard', label: 'Analytics Dashboard', icon: LayoutDashboard, group: 'data' },
    { id: 'settings', label: 'API Settings', icon: Settings, group: 'system' },
  ];

  const groups = [
    { key: 'main', label: 'EXTRACTION ENGINE' },
    { key: 'data', label: 'DATA & ANALYTICS' },
    { key: 'system', label: 'SYSTEM CONFIG' },
  ];

  return (
    <aside style={{
      width: '260px',
      background: '#FFFFFF',
      borderRight: '1px solid #E2E8F0',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      height: '100vh',
      position: 'sticky',
      top: 0,
      zIndex: 30,
      flexShrink: 0,
      userSelect: 'none',
    }}>
      {/* Brand Header */}
      <div>
        <div style={{ padding: '1.25rem 1.25rem 1.15rem', borderBottom: '1px solid #F1F5F9' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: 36, 
              height: 36, 
              borderRadius: 10,
              background: '#4F46E5',
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              boxShadow: '0 2px 4px rgba(79, 70, 229, 0.2)',
              flexShrink: 0,
            }}>
              <Bot size={20} color="white" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontWeight: 800, fontSize: 15, color: '#0F172A', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
                  Agentic AI
                </span>
                <span style={{
                  fontSize: 9, 
                  fontWeight: 700, 
                  padding: '1px 6px',
                  background: '#EEF2FF', 
                  color: '#4338CA',
                  borderRadius: 4, 
                  border: '1px solid #C7D2FE', 
                  letterSpacing: '0.04em'
                }}>PRO</span>
              </div>
              <p style={{ fontSize: 11, color: '#64748B', fontWeight: 500, margin: 0, marginTop: 2 }}>
                Data Extraction Engine
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Section */}
        <nav style={{ padding: '1rem 0.75rem' }}>
          {groups.map(group => {
            const items = navItems.filter(i => i.group === group.key);
            return (
              <div key={group.key} style={{ marginBottom: '1.35rem' }}>
                <div style={{ 
                  fontSize: 10, 
                  fontWeight: 700, 
                  color: '#94A3B8', 
                  letterSpacing: '0.08em', 
                  padding: '0 0.6rem', 
                  marginBottom: '0.4rem' 
                }}>
                  {group.label}
                </div>
                {items.map(item => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      style={{
                        width: '100%', 
                        display: 'flex', 
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.6rem 0.75rem', 
                        borderRadius: 8,
                        borderLeft: isActive ? '3px solid #4F46E5' : '3px solid transparent',
                        background: isActive ? '#EEF2FF' : 'transparent',
                        color: isActive ? '#4338CA' : '#475569',
                        fontSize: 13, 
                        fontWeight: isActive ? 700 : 500, 
                        cursor: 'pointer',
                        transition: 'all 0.15s ease-in-out', 
                        marginBottom: 2,
                      }}
                      onMouseEnter={e => { 
                        if (!isActive) { 
                          (e.currentTarget as HTMLButtonElement).style.background = '#F8FAFC'; 
                          (e.currentTarget as HTMLButtonElement).style.color = '#0F172A'; 
                        } 
                      }}
                      onMouseLeave={e => { 
                        if (!isActive) { 
                          (e.currentTarget as HTMLButtonElement).style.background = 'transparent'; 
                          (e.currentTarget as HTMLButtonElement).style.color = '#475569'; 
                        } 
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <Icon size={17} color={isActive ? '#4F46E5' : '#64748B'} />
                        <span>{item.label}</span>
                      </div>
                      {item.badge && (
                        <span style={{
                          fontSize: 11, 
                          fontWeight: 700, 
                          padding: '1px 7px', 
                          borderRadius: 9999,
                          background: isActive ? '#E0E7FF' : '#F1F5F9', 
                          color: isActive ? '#3730A3' : '#475569',
                          border: '1px solid #C7D2FE',
                        }}>
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div style={{
        padding: '0.85rem 1.25rem',
        borderTop: '1px solid #F1F5F9',
        display: 'flex', 
        alignItems: 'center', 
        gap: 8,
        background: '#FAFAFA'
      }}>
        <Sparkles size={14} color="#4F46E5" />
        <div>
          <div style={{ fontSize: 11, color: '#0F172A', fontWeight: 600 }}>Agentic AI Engine v3.5</div>
          <div style={{ fontSize: 10, color: '#64748B', fontWeight: 500 }}>Multimodal Vision &amp; OpenCV</div>
        </div>
      </div>
    </aside>
  );
};
