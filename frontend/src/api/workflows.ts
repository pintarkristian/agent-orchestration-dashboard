import { API_BASE_URL, apiClient } from './client';
import type { HealthResponse, RunWorkflowRequest, WorkflowRun } from '../types/workflow';

export async function getHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
}

export async function listWorkflows(): Promise<WorkflowRun[]> {
  const response = await apiClient.get<WorkflowRun[]>('/api/workflows');
  return response.data;
}

export async function getWorkflow(workflowId: string): Promise<WorkflowRun> {
  const response = await apiClient.get<WorkflowRun>(`/api/workflows/${workflowId}`);
  return response.data;
}

export async function runWorkflow(payload: RunWorkflowRequest): Promise<WorkflowRun> {
  const response = await apiClient.post<WorkflowRun>('/api/workflows/run', payload);
  return response.data;
}

export function getWorkflowEventsUrl(workflowId: string): string {
  return `${API_BASE_URL.replace(/\/$/, '')}/api/workflows/${workflowId}/events`;
}
