export type WorkflowStatus = 'pending' | 'running' | 'completed' | 'failed';

export type AgentRole =
  | 'planner'
  | 'researcher'
  | 'technical_architect'
  | 'developer'
  | 'reviewer'
  | 'final_answer';

export type WorkflowEventType =
  | 'workflow_started'
  | 'agent_pending'
  | 'agent_running'
  | 'agent_completed'
  | 'agent_failed'
  | 'workflow_completed'
  | 'workflow_failed';

export type WorkflowValue = string | Record<string, unknown> | null;

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface WorkflowStep {
  id: string;
  role: AgentRole;
  name: string;
  description?: string | null;
  input?: WorkflowValue;
  output?: WorkflowValue;
  status: WorkflowStatus;
  error?: string | null;
  created_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
}

export interface WorkflowRun {
  id: string;
  input?: WorkflowValue;
  task?: string;
  output?: WorkflowValue;
  status: WorkflowStatus;
  steps: WorkflowStep[];
  final_answer?: string | null;
  error?: string | null;
  created_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  total_duration_ms?: number | null;
}

export interface WorkflowEvent {
  id: string;
  workflow_id: string;
  event: WorkflowEventType;
  status?: WorkflowStatus | null;
  role?: AgentRole | null;
  step?: WorkflowStep | null;
  workflow?: WorkflowRun | null;
  message?: string | null;
  created_at: string;
}

export interface RunWorkflowRequest {
  task: string;
  workflow_id?: string;
}
