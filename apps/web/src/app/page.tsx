'use client';

import React, { useState } from 'react';
import { Sidebar } from '../components/Sidebar';
import { AgentPlayground } from '../components/AgentPlayground';
import { OverviewDashboard } from '../components/OverviewDashboard';
import { TraceExplorer } from '../components/TraceExplorer';
import { EvaluationStudio } from '../components/EvaluationStudio';
import { AgentMonitoring } from '../components/AgentMonitoring';

export default function Home() {
  const [currentTab, setCurrentTab] = useState('playground');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [targetTraceId, setTargetTraceId] = useState<string | undefined>(undefined);

  const handleOpenTrace = (traceId: string) => {
    setTargetTraceId(traceId);
    setCurrentTab('traces');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090E1A]">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setTargetTraceId(undefined);
          setCurrentTab(tab);
        }}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* Primary Work Area */}
      <main className="flex-1 flex overflow-hidden">
        {currentTab === 'overview' && <OverviewDashboard />}
        {currentTab === 'playground' && <AgentPlayground onOpenTrace={handleOpenTrace} />}
        {currentTab === 'traces' && (
          <TraceExplorer
            selectedTraceId={targetTraceId}
            onCloseDetail={() => setTargetTraceId(undefined)}
          />
        )}
        {currentTab === 'evaluations' && <EvaluationStudio />}
        {currentTab === 'agents' && <AgentMonitoring />}
        {currentTab === 'monitoring' && <AgentMonitoring />}
        {currentTab === 'projects' && <OverviewDashboard />}
        {currentTab === 'settings' && <AgentMonitoring />}
      </main>
    </div>
  );
}
