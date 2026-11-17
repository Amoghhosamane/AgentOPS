'use client';

import React from 'react';
import {
  LayoutDashboard,
  PlayCircle,
  Network,
  CheckCircle2,
  Bot,
  Activity,
  FolderGit2,
  Settings,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export function Sidebar({ currentTab, onSelectTab, isCollapsed, onToggleCollapse }: SidebarProps) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'playground', label: 'Agent Playground', icon: PlayCircle },
    { id: 'traces', label: 'Traces', icon: Network },
    { id: 'evaluations', label: 'Evaluations', icon: CheckCircle2 },
    { id: 'agents', label: 'Agents', icon: Bot },
    { id: 'monitoring', label: 'Monitoring', icon: Activity },
    { id: 'projects', label: 'Projects', icon: FolderGit2 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside
      className={`h-screen bg-[#111827] border-r border-gray-800 transition-all duration-200 flex flex-col ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-sm flex-shrink-0">
            AO
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-sm tracking-wide text-white">AgentOps</span>
              <span className="text-[10px] text-blue-400 font-mono tracking-wider uppercase">Enterprise</span>
            </div>
          )}
        </div>
        <button
          onClick={onToggleCollapse}
          className="p-1 rounded text-gray-400 hover:text-white hover:bg-gray-800 transition"
          title="Toggle Navigation"
        >
          <ChevronRight className={`w-4 h-4 transition-transform ${isCollapsed ? '' : 'rotate-180'}`} />
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
              title={isCollapsed ? item.label : undefined}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {!isCollapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      {!isCollapsed && (
        <div className="p-4 border-t border-gray-800 bg-[#0d131f]">
          <div className="flex items-center space-x-2 text-xs text-gray-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span className="truncate">OTel Ingestion Active</span>
          </div>
          <div className="mt-1 text-[11px] text-gray-500 font-mono">Project: Production Agents</div>
        </div>
      )}
    </aside>
  );
}
