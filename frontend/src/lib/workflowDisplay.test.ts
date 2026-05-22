import { describe, expect, it } from 'vitest';
import {
  formatDuration,
  formatWorkflowValue,
  getStepTitle,
  getWorkflowFinalAnswer,
  roleLabels,
  truncateText,
} from './workflowDisplay';
import type { WorkflowRun, WorkflowStep } from '../types/workflow';

describe('workflow display helpers', () => {
  it('formats empty, string, and object values for display', () => {
    expect(formatWorkflowValue(null)).toBe('No content returned.');
    expect(formatWorkflowValue('Planner output')).toBe('Planner output');
    expect(formatWorkflowValue({ status: 'ready' })).toBe('{\n  "status": "ready"\n}');
  });

  it('formats durations across empty, millisecond, and second values', () => {
    expect(formatDuration(undefined)).toBe('-');
    expect(formatDuration(425)).toBe('425 ms');
    expect(formatDuration(1250)).toBe('1.25 s');
    expect(formatDuration(12000)).toBe('12.0 s');
  });

  it('uses workflow final answer, output, error, then fallback text', () => {
    const baseWorkflow: WorkflowRun = {
      id: 'workflow-1',
      status: 'completed',
      steps: [],
    };

    expect(getWorkflowFinalAnswer({ ...baseWorkflow, final_answer: 'Final answer' })).toBe(
      'Final answer',
    );
    expect(getWorkflowFinalAnswer({ ...baseWorkflow, output: 'Output' })).toBe('Output');
    expect(getWorkflowFinalAnswer({ ...baseWorkflow, error: 'Failed' })).toBe('Failed');
    expect(getWorkflowFinalAnswer(baseWorkflow)).toBe('No final answer returned.');
  });

  it('builds readable step titles from explicit names, role labels, and role fallbacks', () => {
    const step: WorkflowStep = {
      id: 'step-1',
      role: 'planner',
      name: '',
      status: 'pending',
    };

    expect(roleLabels.planner).toBe('Planner Agent');
    expect(getStepTitle({ ...step, name: 'Custom Planner' })).toBe('Custom Planner');
    expect(getStepTitle(step)).toBe('Planner Agent');
  });

  it('truncates long text without changing short text', () => {
    expect(truncateText('Short text', 20)).toBe('Short text');
    expect(truncateText('This text is too long for a compact card', 17)).toBe(
      'This text is too...',
    );
  });
});
