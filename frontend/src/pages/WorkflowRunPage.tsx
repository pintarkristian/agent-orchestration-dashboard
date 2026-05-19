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
import { getApiErrorMessage } from '../lib/workflowDisplay';

const defaultTask = 'Analyze this startup idea and create a technical implementation plan.';

export default function WorkflowRunPage() {
  const [task, setTask] = useState(defaultTask);
  const [validationError, setValidationError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const workflowMutation = useMutation({
    mutationFn: runWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  const taskLength = useMemo(() => task.trim().length, [task]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedTask = task.trim();
    if (!trimmedTask) {
      setValidationError('Enter a task before running the workflow.');
      return;
    }

    setValidationError(null);
    workflowMutation.mutate({ task: trimmedTask });
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
              This calls <code className="rounded bg-slate-100 px-1 py-0.5">POST /api/workflows/run</code> and stores the run in SQLite.
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

      {workflowMutation.isPending && (
        <LoadingState
          title="Workflow running"
          message="The specialized agents are processing the task. Longer requests can take a little while."
        />
      )}

      {workflowMutation.isError && (
        <ErrorState
          title="Workflow request failed"
          message={getApiErrorMessage(workflowMutation.error)}
        />
      )}

      {workflowMutation.data && (
        <div className="space-y-6">
          <WorkflowResultCard workflow={workflowMutation.data} />

          <WorkflowGraph workflow={workflowMutation.data} />

          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h3 className="text-xl font-semibold text-slate-950">Agent Steps</h3>
              <p className="mt-1 text-sm text-slate-500">
                Each card shows the prompt input, generated output, status, duration, and any error returned by the backend.
              </p>
            </div>
            <Link
              to={`/workflows/${workflowMutation.data.id}`}
              className="inline-flex items-center justify-center rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-950 hover:text-slate-950"
            >
              Open saved detail
            </Link>
          </div>

          <div className="space-y-5">
            {workflowMutation.data.steps.map((step, index) => (
              <AgentStepCard key={step.id} step={step} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
