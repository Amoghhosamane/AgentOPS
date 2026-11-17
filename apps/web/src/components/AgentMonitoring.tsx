'use client';

import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  Clock,
  Cpu,
  Layers,
  ShieldAlert
} from 'lucide-react';
import { fetchAgents, fetchAlerts, DEFAULT_PROJECT_ID } from '../lib/api';

export function AgentMonitoring() {
  const [agents, setAgents] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchAgents(DEFAULT_PROJECT_ID), fetchAlerts(DEFAULT_PROJECT_ID)])
      .then(([ag, al]) => {
        setAgents(ag);
        setAlerts(al);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-[#090E1A] space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Agent Health & Runtime Monitoring</h1>
        <p className="text-sm text-gray-400 mt-1">
          Active alerts, rate-limit thresholds, and agent runtime operational status.
        </p>
      </div>

      {/* Active Alerts Section */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span>Active Alerts & System Notices</span>
        </h2>

        {alerts.length === 0 ? (
          <div className="p-4 bg-gray-900 border border-gray-800 rounded-lg text-xs text-gray-400">
            No active alerts or warnings triggered.
          </div>
        ) : (
          alerts.map((al) => (
            <div
              key={al.id}
              className="p-4 bg-[#111827] border border-gray-800 rounded-xl flex items-start space-x-3"
            >
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold text-white">{al.title}</div>
                <div className="text-xs text-gray-400 mt-0.5">{al.message}</div>
                <div className="text-[11px] text-gray-500 font-mono mt-2">Source: {al.source}</div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Registered Agents Fleet */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider flex items-center space-x-2">
          <Bot className="w-4 h-4 text-blue-400" />
          <span>Registered Agent Services ({agents.length})</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {agents.map((ag) => (
            <div key={ag.id} className="p-5 bg-[#111827] border border-gray-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-white">{ag.name}</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-800/60">
                  HEALTHY
                </span>
              </div>

              <p className="text-xs text-gray-400 leading-relaxed">{ag.description}</p>

              <div className="pt-2 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500 font-mono">
                <span>Model: {ag.default_model}</span>
                <span>Type: {ag.agent_type}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
