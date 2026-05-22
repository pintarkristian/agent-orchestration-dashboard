import type { FormEvent } from 'react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { runWorkflow } from '../api/workflows';
import { AgentStepCard } from '../components/workflows/AgentStepCard';
import { WorkflowResultCard } from '../components/workflows/WorkflowResultCard';
import { WorkflowGraph } from '../components/workflows/WorkflowGraph';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useWorkflowEvents } from '../hooks/useWorkflowEvents';
import { getApiErrorMessage } from '../lib/workflowDisplay';

const defaultTask = 'Analyze this startup idea and create a technical implementation plan.';

function createWorkflowId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }

  return `workflow-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function WorkflowRunPage() {
  const [task, setTask] = useState(defaultTask);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const workflowMutation = useMutation({
    mutationFn: runWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  const liveUpdatesEnabled = Boolean(activeWorkflowId && workflowMutation.isPending);
  const {
    workflow: liveWorkflow,
    events: liveEvents,
    isConnected,
    connectionError,
  } = useWorkflowEvents(activeWorkflowId, liveUpdatesEnabled);

  const taskLength = useMemo(() => task.trim().length, [task]);
  const completedWorkflow = workflowMutation.data?.id === activeWorkflowId ? workflowMutation.data : null;
  const visibleWorkflow = completedWorkflow ?? liveWorkflow;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedTask = task.trim();
    if (!trimmedTask) {
      setValidationError('Enter a task before running the workflow.');
      return;
    }

    const workflowId = createWorkflowId();
    setValidationError(null);
    setActiveWorkflowId(workflowId);
    workflowMutation.reset();
    workflowMutation.mutate({ task: trimmedTask, workflow_id: workflowId });
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Run Workflow</p>
        <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Run a multi-agent orchestration task</h2>
        <p className="mt-3 max-w-3xl text-slate-600">
          Enter a complex request and the backend will send it through the planner, researcher, technical architect,
          developer, reviewer, and final answer agents.
        </p>
      </div>

      <Card title="New Task" eyebrow="Input">
        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <div className="flex items-center justify-between gap-4">
              <label htmlFor="task" className="text-sm font-medium text-slate-700">
                User task
              </label>
              <span className="text-xs text-slate-400">{taskLength} characters</span>
            </div>
            <textarea
              id="task"
              rows={8}
              value={task}
              onChange={(event) => setTask(event.target.value)}
              placeholder="Analyze this startup idea and create a technical implementation plan."
              className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm leading-6 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-950 focus:ring-4 focus:ring-slate-200"
            />
            {validationError && <p className="mt-2 text-sm text-rose-600">{validationError}</p>}
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-slate-500">
              This calls <code className="rounded bg-slate-100 px-1 py-0.5">POST /api/workflows/run</code>, stores the run in SQLite,
              and listens to live SSE events while agents execute.
            </p>
            <button
              type="submit"
              disabled={workflowMutation.isPending || taskLength === 0}
              className="inline-flex items-center justify-center rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {workflowMutation.isPending ? 'Running workflow...' : 'Run workflow'}
            </button>
          </div>
        </form>
      </Card>

      {workflowMutation.isPending && !visibleWorkflow && (
        <LoadingState
          title="Workflow starting"
          message="Opening the live event stream and preparing the specialized agents."
        />
      )}

      {workflowMutation.isPending && visibleWorkflow && (
        <Card
          title="Live workflow status"
          eyebrow="Real-time Updates"
          actions={<StatusBadge status={visibleWorkflow.status} />}
        >
          <div className="grid gap-3 text-sm sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Connection</p>
              <p className="mt-1 font-medium text-slate-900">{isConnected ? 'Connected' : 'Connecting / fallback ready'}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Events received</p>
              <p className="mt-1 font-medium text-slate-900">{liveEvents.length}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Workflow ID</p>
              <p className="mt-1 break-all font-medium text-slate-900">{visibleWorkflow.id}</p>
            </div>
          </div>
          {connectionError && (
            <p className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              {connectionError}
            </p>
          )}
        </Card>
      )}

      {workflowMutation.isError && (
        <ErrorState
          title="Workflow request failed"
          message={getApiErrorMessage(workflowMutation.error)}
        />
      )}

      {visibleWorkflow && (
        <div className="space-y-6">
          {completedWorkflow && <WorkflowResultCard workflow={completedWorkflow} />}

          <WorkflowGraph workflow={visibleWorkflow} />

          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h3 className="text-xl font-semibold text-slate-950">Agent Steps</h3>
              <p className="mt-1 text-sm text-slate-500">
                Live cards update as each agent starts and completes. The final POST response remains the fallback source of truth.
              </p>
            </div>
            {completedWorkflow && (
              <Link
                to={`/workflows/${completedWorkflow.id}`}
                className="inline-flex items-center justify-center rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-950 hover:text-slate-950"
              >
                Open saved detail
              </Link>
            )}
          </div>

          <div className="space-y-5">
            {visibleWorkflow.steps.map((step, index) => (
              <AgentStepCard key={`${step.role}-${step.id}`} step={step} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
