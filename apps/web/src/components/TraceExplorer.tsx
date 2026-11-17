'use client';

import React, { useState, useEffect } from 'react';
import {
  Network,
  Clock,
  Coins,
  CheckCircle2,
  XCircle,
  Filter,
  ArrowRight,
  ChevronDown,
  Layers,
  Wrench,
  Cpu
} from 'lucide-react';
import { fetchTraces, fetchTraceDetail, DEFAULT_PROJECT_ID } from '../lib/api';

export function TraceExplorer({ selectedTraceId, onCloseDetail }: { selectedTraceId?: string; onCloseDetail?: () => void }) {
  const [traces, setTraces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTraceId, setActiveTraceId] = useState<string | null>(selectedTraceId || null);
  const [activeTraceDetail, setActiveTraceDetail] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('');

  const loadTraces = async () => {
    setLoading(true);
    try {
      const data = await fetchTraces(DEFAULT_PROJECT_ID, filterStatus);
      setTraces(data.traces || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTraces();
  }, [filterStatus]);

  useEffect(() => {
    if (activeTraceId) {
      setDetailLoading(true);
      fetchTraceDetail(activeTraceId)
        .then((data) => setActiveTraceDetail(data))
        .catch((e) => console.error(e))
        .finally(() => setDetailLoading(false));
    } else {
      setActiveTraceDetail(null);
    }
  }, [activeTraceId]);

  return (
    <div className="flex-1 flex overflow-hidden bg-[#090E1A]">
      {/* Left List of Traces */}
      <div className={`border-r border-gray-800 flex flex-col ${activeTraceId ? 'w-1/2' : 'w-full'} transition-all duration-200`}>
        {/* Header and Filter */}
        <div className="p-4 border-b border-gray-800 bg-[#111827] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Network className="w-5 h-5 text-blue-400" />
            <h1 className="text-sm font-semibold text-white">Distributed Traces</h1>
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-gray-800 border border-gray-700 text-xs rounded px-2.5 py-1 text-gray-300 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="ok">Success (ok)</option>
              <option value="error">Errors</option>
            </select>
          </div>
        </div>

        {/* Traces Table / List */}
        <div className="flex-1 overflow-y-auto divide-y divide-gray-800/60">
          {loading ? (
            <div className="p-8 text-center text-xs text-gray-500">Loading trace spans...</div>
          ) : traces.length === 0 ? (
            <div className="p-8 text-center text-xs text-gray-500">No traces found for filter.</div>
          ) : (
            traces.map((t) => {
              const isSelected = t.id === activeTraceId;
              return (
                <div
                  key={t.id}
                  onClick={() => setActiveTraceId(t.id)}
                  className={`p-4 cursor-pointer hover:bg-gray-800/50 transition-colors ${
                    isSelected ? 'bg-gray-800/80 border-l-2 border-blue-500' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {t.status === 'ok' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                      <span className="text-sm font-medium text-white truncate max-w-xs">{t.name}</span>
                      {t.is_synthetic && (
                        <span className="text-[10px] text-amber-400 bg-amber-950/40 border border-amber-800/60 px-1.5 py-0.5 rounded">
                          Synthetic Demo
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-mono text-gray-400">{t.duration_ms} ms</span>
                  </div>

                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 font-mono">
                    <span>ID: {t.id.slice(0, 12)}...</span>
                    <span>Spans: {t.total_spans}</span>
                    <span>Tokens: {t.total_tokens}</span>
                    <span>Cost: ${t.estimated_cost}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Waterfall Detail Pane */}
      {activeTraceId && (
        <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[#0d131f]">
          <div className="p-4 border-b border-gray-800 bg-[#111827] flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white">Execution Waterfall</h2>
              <div className="text-xs text-gray-400 font-mono mt-0.5">Trace ID: {activeTraceId}</div>
            </div>
            <button
              onClick={() => {
                setActiveTraceId(null);
                if (onCloseDetail) onCloseDetail();
              }}
              className="text-xs text-gray-400 hover:text-white px-2 py-1 bg-gray-800 rounded"
            >
              Close
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {detailLoading ? (
              <div className="text-xs text-gray-500 text-center py-8">Loading waterfall spans...</div>
            ) : activeTraceDetail ? (
              <div className="space-y-4">
                {/* Waterfall Visual Bars */}
                <div className="p-4 bg-gray-900 border border-gray-800 rounded-xl space-y-3">
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Span Hierarchy & Durations
                  </div>

                  <div className="space-y-3 pt-2">
                    {activeTraceDetail.spans.map((s: any, idx: number) => {
                      const maxDur = activeTraceDetail.duration_ms || 1;
                      const widthPercent = Math.max(12, Math.min(100, Math.round((s.duration_ms / maxDur) * 100)));

                      return (
                        <div key={s.span_id || idx} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-mono text-gray-200 flex items-center space-x-1.5">
                              {s.operation_name === 'tool.execute' ? (
                                <Wrench className="w-3.5 h-3.5 text-amber-400" />
                              ) : s.operation_name === 'chat' ? (
                                <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                              ) : (
                                <Layers className="w-3.5 h-3.5 text-blue-400" />
                              )}
                              <span>{s.name}</span>
                            </span>
                            <span className="font-mono text-gray-400">{s.duration_ms} ms</span>
                          </div>

                          {/* Horizontal Waterfall Bar */}
                          <div className="w-full bg-gray-800 h-3 rounded-full overflow-hidden flex">
                            <div
                              style={{ width: `${widthPercent}%` }}
                              className={`h-full rounded-full ${
                                s.status === 'ok' ? 'bg-blue-500' : 'bg-red-500'
                              }`}
                            />
                          </div>

                          {/* Metadata Preview */}
                          <div className="text-[11px] text-gray-500 font-mono flex items-center space-x-3">
                            {s.gen_ai_model && <span>Model: {s.gen_ai_model}</span>}
                            {s.total_tokens > 0 && <span>Tokens: {s.total_tokens}</span>}
                            {s.tool_name && <span className="text-amber-300">Tool: {s.tool_name}</span>}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
