import { useEffect, useMemo, useState } from 'react';
import { getWorkflowEventsUrl } from '../api/workflows';
import type { WorkflowEvent, WorkflowEventType, WorkflowRun, WorkflowStep } from '../types/workflow';

const workflowEventTypes: WorkflowEventType[] = [
  'workflow_started',
  'agent_pending',
  'agent_running',
  'agent_completed',
  'agent_failed',
  'workflow_completed',
  'workflow_failed',
];

const terminalEvents: WorkflowEventType[] = ['workflow_completed', 'workflow_failed'];

function emptyWorkflow(workflowId: string): WorkflowRun {
  return {
    id: workflowId,
    input: null,
    output: null,
    final_answer: null,
    status: 'running',
    steps: [],
    error: null,
    created_at: null,
    started_at: null,
    completed_at: null,
    duration_ms: null,
    total_duration_ms: null,
  };
}

function upsertStep(steps: WorkflowStep[], nextStep: WorkflowStep): WorkflowStep[] {
  const index = steps.findIndex((step) => step.role === nextStep.role);

  if (index === -1) {
    return [...steps, nextStep];
  }

  const updatedSteps = [...steps];
  updatedSteps[index] = {
    ...updatedSteps[index],
    ...nextStep,
  };
  return updatedSteps;
}

function applyWorkflowEvent(previous: WorkflowRun | null, event: WorkflowEvent): WorkflowRun {
  if (event.workflow) {
    return event.workflow;
  }

  const base = previous ?? emptyWorkflow(event.workflow_id);
  const steps = event.step ? upsertStep(base.steps, event.step) : base.steps;

  return {
    ...base,
    status: event.status ?? base.status,
    error: event.event === 'workflow_failed' ? event.message ?? base.error : base.error,
    steps,
  };
}

interface UseWorkflowEventsResult {
  workflow: WorkflowRun | null;
  events: WorkflowEvent[];
  isConnected: boolean;
  connectionError: string | null;
}

export function useWorkflowEvents(workflowId: string | null, enabled: boolean): UseWorkflowEventsResult {
  const [workflow, setWorkflow] = useState<WorkflowRun | null>(null);
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const url = useMemo(() => (workflowId ? getWorkflowEventsUrl(workflowId) : null), [workflowId]);

  useEffect(() => {
    setWorkflow(null);
    setEvents([]);
    setIsConnected(false);
    setConnectionError(null);

    if (!enabled || !workflowId || !url) {
      return undefined;
    }

    const source = new EventSource(url);
    let closedByTerminalEvent = false;

    source.onopen = () => {
      setIsConnected(true);
      setConnectionError(null);
    };

    const handleMessage = (message: MessageEvent<string>) => {
      try {
        const event = JSON.parse(message.data) as WorkflowEvent;
        setEvents((currentEvents) => [...currentEvents, event]);
        setWorkflow((currentWorkflow) => applyWorkflowEvent(currentWorkflow, event));

        if (terminalEvents.includes(event.event)) {
          closedByTerminalEvent = true;
          setIsConnected(false);
          source.close();
        }
      } catch (error) {
        setConnectionError(error instanceof Error ? error.message : 'Could not parse workflow event.');
      }
    };

    workflowEventTypes.forEach((eventType) => {
      source.addEventListener(eventType, handleMessage as EventListener);
    });

    source.onerror = () => {
      setIsConnected(false);
      source.close();
      if (!closedByTerminalEvent) {
        setConnectionError('Real-time workflow connection failed. The final API response will still be shown when available.');
      }
    };

    return () => {
      workflowEventTypes.forEach((eventType) => {
        source.removeEventListener(eventType, handleMessage as EventListener);
      });
      source.close();
    };
  }, [enabled, workflowId, url]);

  return { workflow, events, isConnected, connectionError };
}
