'use client';

import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  XCircle,
  Play,
  RotateCw,
  FolderPlus,
  Layers,
  ChevronRight,
  TrendingUp,
  FileCheck
} from 'lucide-react';
import { fetchEvaluationDatasets, fetchEvaluationRuns, triggerEvaluationRun, DEFAULT_PROJECT_ID } from '../lib/api';

export function EvaluationStudio() {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [selectedRun, setSelectedRun] = useState<any>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ds, r] = await Promise.all([
        fetchEvaluationDatasets(DEFAULT_PROJECT_ID),
        fetchEvaluationRuns(DEFAULT_PROJECT_ID),
      ]);
      setDatasets(ds);
      setRuns(r);
      if (r.length > 0 && !selectedRun) {
        setSelectedRun(r[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunEvaluation = async (datasetId: string) => {
    setEvaluating(true);
    try {
      const newRun = await triggerEvaluationRun(DEFAULT_PROJECT_ID, datasetId);
      setRuns((prev) => [newRun, ...prev]);
      setSelectedRun(newRun);
    } catch (e) {
      console.error(e);
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#090E1A]">
      {/* Left List of Datasets & Past Runs */}
      <div className="w-1/3 border-r border-gray-800 flex flex-col bg-[#111827]">
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileCheck className="w-5 h-5 text-blue-400" />
            <h1 className="text-sm font-semibold text-white">Evaluation Studio</h1>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Datasets Section */}
          <div className="space-y-3">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Golden Test Datasets
            </h2>
            {datasets.map((d) => (
              <div key={d.id} className="p-3 bg-gray-900 border border-gray-800 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-white">{d.name}</span>
                  <span className="text-[10px] font-mono text-gray-400 bg-gray-800 px-1.5 py-0.5 rounded">
                    v{d.version}
                  </span>
                </div>
                <p className="text-xs text-gray-400">{d.description}</p>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-xs text-gray-500">{d.test_cases?.length || 0} Test Cases</span>
                  <button
                    onClick={() => handleRunEvaluation(d.id)}
                    disabled={evaluating}
                    className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-medium transition"
                  >
                    <Play className="w-3 h-3" />
                    <span>{evaluating ? 'Running...' : 'Run Benchmark'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Historical Runs */}
          <div className="space-y-3">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Historical Benchmark Runs
            </h2>
            {runs.map((r) => {
              const isSelected = selectedRun?.id === r.id;
              return (
                <div
                  key={r.id}
                  onClick={() => setSelectedRun(r)}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    isSelected
                      ? 'bg-gray-800 border-blue-500'
                      : 'bg-gray-900/60 border-gray-800 hover:bg-gray-800/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-white">Version: {r.agent_version}</span>
                    <span
                      className={`text-xs font-semibold ${
                        r.pass_rate >= 80 ? 'text-emerald-400' : 'text-amber-400'
                      }`}
                    >
                      {r.pass_rate}% Pass
                    </span>
                  </div>
                  <div className="text-[11px] text-gray-400 mt-1 flex items-center justify-between font-mono">
                    <span>Passed: {r.passed_cases}/{r.total_cases}</span>
                    <span>Avg: {r.average_latency_ms}ms</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right Run Details Pane */}
      <div className="flex-1 flex flex-col overflow-hidden bg-[#0d131f] p-6 space-y-6">
        {selectedRun ? (
          <>
            {/* Run Header KPI */}
            <div className="p-5 bg-[#111827] border border-gray-800 rounded-xl flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white">Benchmark Report</h2>
                <div className="text-xs text-gray-400 font-mono mt-0.5">Run ID: {selectedRun.id}</div>
              </div>

              <div className="flex items-center space-x-6">
                <div className="text-right">
                  <div className="text-xs text-gray-400">Pass Rate</div>
                  <div className="text-xl font-bold text-emerald-400">{selectedRun.pass_rate}%</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-400">Avg Latency</div>
                  <div className="text-xl font-bold text-white font-mono">{selectedRun.average_latency_ms} ms</div>
                </div>
              </div>
            </div>

            {/* Test Case Results Table */}
            <div className="flex-1 overflow-y-auto space-y-3">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Case-by-Case Diagnostic Assertions
              </h3>

              {selectedRun.results?.map((res: any, idx: number) => (
                <div key={res.id || idx} className="p-4 bg-gray-900 border border-gray-800 rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {res.status === 'passed' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                      <span className="text-xs font-semibold text-white">Test Case #{idx + 1}</span>
                    </div>
                    <span className="text-xs font-mono text-gray-400">{res.latency_ms} ms</span>
                  </div>

                  {/* Diagnostic Output */}
                  <div className="p-2 bg-black/40 rounded text-xs font-mono text-gray-300 overflow-x-auto">
                    {res.actual_output}
                  </div>

                  {/* Evaluator Scores Breakdown */}
                  <div className="flex flex-wrap gap-2 pt-1">
                    {Object.entries(res.scores || {}).map(([metric, score]: any) => (
                      <span
                        key={metric}
                        className="text-[11px] font-mono px-2 py-0.5 rounded bg-gray-800 text-gray-300 border border-gray-700"
                      >
                        {metric}: {(score * 100).toFixed(0)}%
                      </span>
                    ))}
                  </div>

                  {/* Failure Reasons */}
                  {res.reasons && res.reasons.length > 0 && (
                    <div className="text-[11px] text-red-400 pt-1">
                      {res.reasons.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-xs text-gray-500">
            Select an evaluation run to view diagnostic breakdown.
          </div>
        )}
      </div>
    </div>
  );
}
