'use client';

import React, { useState, useEffect } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Coins,
  Cpu,
  BarChart3,
  TrendingUp,
  RefreshCw
} from 'lucide-react';
import { fetchMetricsOverview, DEFAULT_PROJECT_ID } from '../lib/api';

export function OverviewDashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMetricsOverview(DEFAULT_PROJECT_ID);
      setMetrics(data);
    } catch (e: any) {
      setError(e.message || 'Failed to fetch telemetry metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-[#090E1A] space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">System Observability Overview</h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time telemetry, latency percentiles, and token consumption aggregates.
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-gray-800 border border-gray-700 text-xs font-medium text-gray-300 hover:text-white hover:bg-gray-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadData} className="underline text-xs">Retry</button>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* Total Runs */}
        <div className="p-5 bg-[#111827] border border-gray-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Total Agent Runs</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : metrics?.total_agent_runs || 0}
          </div>
          <div className="text-xs text-gray-500">Live & synthetic recorded runs</div>
        </div>

        {/* Success Percentage */}
        <div className="p-5 bg-[#111827] border border-gray-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Success Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : `${metrics?.success_rate || 0}%`}
          </div>
          <div className="text-xs text-emerald-400 font-medium">Within target SLA threshold</div>
        </div>

        {/* p95 Latency */}
        <div className="p-5 bg-[#111827] border border-gray-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>p95 Latency</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : `${metrics?.p95_latency_ms || 0} ms`}
          </div>
          <div className="text-xs text-gray-500">Tail execution duration</div>
        </div>

        {/* Total Tokens */}
        <div className="p-5 bg-[#111827] border border-gray-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Total Tokens Consumed</span>
            <Cpu className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : (metrics?.total_tokens || 0).toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">Prompt & completion usage</div>
        </div>

        {/* Estimated Cost */}
        <div className="p-5 bg-[#111827] border border-gray-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Estimated Cost</span>
            <Coins className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : `$${metrics?.estimated_cost || 0}`}
          </div>
          <div className="text-xs text-gray-500">Based on blended model rates</div>
        </div>

        {/* Eval Pass Rate */}
        <div className="p-5 bg-[#111827] border border-gray-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-gray-400 text-xs font-medium">
            <span>Evaluation Pass Rate</span>
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {loading ? '...' : `${metrics?.eval_pass_rate || 0}%`}
          </div>
          <div className="text-xs text-gray-500">Regression benchmark accuracy</div>
        </div>
      </div>

      {/* Latency Percentiles & Tokens Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latency Percentiles Table */}
        <div className="p-6 bg-[#111827] border border-gray-800 rounded-xl space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
            <Clock className="w-4 h-4 text-blue-400" />
            <span>Execution Latency Percentiles</span>
          </h2>

          <div className="space-y-3 pt-2">
            {metrics?.latency_percentiles &&
              Object.entries(metrics.latency_percentiles).map(([p, val]: any) => (
                <div key={p} className="flex items-center justify-between text-xs py-2 border-b border-gray-800">
                  <span className="font-mono text-gray-400 uppercase">{p}</span>
                  <span className="font-mono font-semibold text-white">{val} ms</span>
                </div>
              ))}
          </div>
        </div>

        {/* Tokens by Model */}
        <div className="p-6 bg-[#111827] border border-gray-800 rounded-xl space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <span>Token Volume by Model</span>
          </h2>

          <div className="space-y-3 pt-2">
            {metrics?.tokens_by_model?.map((item: any) => (
              <div key={item.model} className="flex items-center justify-between text-xs py-2 border-b border-gray-800">
                <span className="font-mono text-gray-300">{item.model}</span>
                <span className="font-mono text-blue-400 font-semibold">{item.tokens.toLocaleString()} tokens</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
