import { isAxiosError } from 'axios';
import type { AgentRole, WorkflowRun, WorkflowStep, WorkflowValue } from '../types/workflow';

export const roleLabels: Record<AgentRole, string> = {
  planner: 'Planner Agent',
  researcher: 'Research Agent',
  technical_architect: 'Technical Architect Agent',
  developer: 'Developer Agent',
  reviewer: 'Reviewer Agent',
  final_answer: 'Final Answer Agent',
};

export function formatWorkflowValue(value: WorkflowValue | undefined): string {
  if (value === null || value === undefined || value === '') {
    return 'No content returned.';
  }

  if (typeof value === 'string') {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

export function formatDuration(durationMs?: number | null): string {
  if (durationMs === null || durationMs === undefined) {
    return '-';
  }

  if (durationMs >= 1000) {
    return `${(durationMs / 1000).toFixed(durationMs >= 10000 ? 1 : 2)} s`;
  }

  return `${durationMs} ms`;
}

export function formatDateTime(value?: string | null): string {
  if (!value) {
    return '-';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function getWorkflowTask(workflow: WorkflowRun): string {
  return workflow.task ?? formatWorkflowValue(workflow.input);
}

export function getWorkflowFinalAnswer(workflow: WorkflowRun): string {
  return formatWorkflowValue(workflow.final_answer || workflow.output || workflow.error || 'No final answer returned.');
}

export function getWorkflowDuration(workflow: WorkflowRun): number | null | undefined {
  return workflow.total_duration_ms ?? workflow.duration_ms;
}

export function getStepTitle(step: WorkflowStep): string {
  return step.name || roleLabels[step.role] || step.role.replace('_', ' ');
}

export function getApiErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg ?? JSON.stringify(item)).join(' ');
    }

    return error.message || 'The backend request failed.';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'The backend request failed.';
}

export function truncateText(value: string, maxLength = 140): string {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength).trim()}...`;
}
