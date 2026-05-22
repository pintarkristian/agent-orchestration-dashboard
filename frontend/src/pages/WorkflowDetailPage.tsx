import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getWorkflow } from '../api/workflows';
import { AgentStepCard } from '../components/workflows/AgentStepCard';
import { WorkflowResultCard } from '../components/workflows/WorkflowResultCard';
import { WorkflowGraph } from '../components/workflows/WorkflowGraph';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useWorkflowEvents } from '../hooks/useWorkflowEvents';
import { formatWorkflowValue, getWorkflowTask } from '../lib/workflowDisplay';

export default function WorkflowDetailPage() {
  const { workflowId } = useParams<{ workflowId: string }>();

  const workflowQuery = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: () => getWorkflow(workflowId ?? ''),
    enabled: Boolean(workflowId),
    retry: 1,
  });

  const shouldListenForLiveEvents = Boolean(
    workflowId && (!workflowQuery.data || workflowQuery.data.status === 'pending' || workflowQuery.data.status === 'running'),
  );
  const {
    workflow: liveWorkflow,
    events: liveEvents,
    isConnected,
    connectionError,
  } = useWorkflowEvents(workflowId ?? null, shouldListenForLiveEvents);

  if (!workflowId) {
    return <ErrorState title="Missing workflow ID" message="The selected workflow route does not include an ID." />;
  }

  const visibleWorkflow = liveWorkflow ?? workflowQuery.data;
  const showNotFoundError = workflowQuery.isError && !visibleWorkflow;
  const showLoadingState = workflowQuery.isLoading && !visibleWorkflow;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Workflow Detail</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Saved workflow run</h2>
          <p className="mt-3 max-w-3xl break-all text-sm text-slate-500">{workflowId}</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Link
            to="/workflows"
            className="inline-flex items-center justify-center rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-950 hover:text-slate-950"
          >
            Back to history
          </Link>
          <Link
            to="/workflows/run"
            className="inline-flex items-center justify-center rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Run new workflow
          </Link>
        </div>
      </div>

      {showLoadingState && <LoadingState title="Loading workflow" message="Reading the saved run and agent steps from the backend..." />}
      {showNotFoundError && <ErrorState title="Workflow not found" message="Could not load this workflow. It may have been deleted or the backend may be unavailable." />}

      {(liveWorkflow || connectionError) && (
        <Card
          title="Live update stream"
          eyebrow="Server-Sent Events"
          actions={visibleWorkflow ? <StatusBadge status={visibleWorkflow.status} /> : undefined}
        >
          <div className="grid gap-3 text-sm sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Connection</p>
              <p className="mt-1 font-medium text-slate-900">{isConnected ? 'Connected' : 'Fallback ready'}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Events received</p>
              <p className="mt-1 font-medium text-slate-900">{liveEvents.length}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Workflow ID</p>
              <p className="mt-1 break-all font-medium text-slate-900">{workflowId}</p>
            </div>
          </div>
          {connectionError && (
            <p className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              {connectionError}
            </p>
          )}
        </Card>
      )}

      {visibleWorkflow && (
        <div className="space-y-6">
          <Card
            title="Original Task"
            eyebrow="Request"
            actions={<StatusBadge status={visibleWorkflow.status} />}
          >
            <pre className="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm leading-7 text-slate-800">
              {formatWorkflowValue(getWorkflowTask(visibleWorkflow))}
            </pre>
          </Card>

          {(visibleWorkflow.final_answer || visibleWorkflow.output || visibleWorkflow.status !== 'running') && (
            <WorkflowResultCard workflow={visibleWorkflow} title="Final Answer" eyebrow="Combined Output" />
          )}

          <WorkflowGraph workflow={visibleWorkflow} />

          {visibleWorkflow.error && (
            <ErrorState title="Workflow error" message={visibleWorkflow.error} />
          )}

          <div>
            <h3 className="text-xl font-semibold text-slate-950">Agent Steps</h3>
            <p className="mt-1 text-sm text-slate-500">
              Full execution detail for every specialized agent in the sequential workflow.
            </p>
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
