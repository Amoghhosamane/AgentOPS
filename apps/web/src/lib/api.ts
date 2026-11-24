/** Client SDK and API fetchers connecting to FastAPI backend */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const DEFAULT_PROJECT_ID = 'proj-agentops-demo-001';

export async function fetchMetricsOverview(projectId = DEFAULT_PROJECT_ID) {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/metrics/overview`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load metrics overview');
  return res.json();
}

export async function fetchTraces(projectId = DEFAULT_PROJECT_ID, status = '') {
  const url = `${API_BASE}/api/v1/projects/${projectId}/traces${status ? `?status=${status}` : ''}`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load traces');
  return res.json();
}

export async function fetchTraceDetail(traceId: string) {
  const res = await fetch(`${API_BASE}/api/v1/traces/${traceId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load trace detail');
  return res.json();
}

export async function fetchEvaluationDatasets(projectId = DEFAULT_PROJECT_ID) {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/evaluations/datasets`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load evaluation datasets');
  return res.json();
}

export async function fetchEvaluationRuns(projectId = DEFAULT_PROJECT_ID) {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/evaluations/runs`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load evaluation runs');
  return res.json();
}

export async function triggerEvaluationRun(projectId = DEFAULT_PROJECT_ID, datasetId: string) {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/evaluations/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_id: datasetId, agent_version: '1.0.0' }),
  });
  if (!res.ok) throw new Error('Failed to trigger evaluation run');
  return res.json();
}

export async function fetchAgents(projectId = DEFAULT_PROJECT_ID) {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/agents`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load agents');
  return res.json();
}

export async function fetchAlerts(projectId = DEFAULT_PROJECT_ID) {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/alerts`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load alerts');
  return res.json();
}
