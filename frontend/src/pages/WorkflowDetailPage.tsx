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
import { formatWorkflowValue, getWorkflowTask } from '../lib/workflowDisplay';

export default function WorkflowDetailPage() {
  const { workflowId } = useParams<{ workflowId: string }>();

  const workflowQuery = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: () => getWorkflow(workflowId ?? ''),
    enabled: Boolean(workflowId),
    retry: 1,
  });

  if (!workflowId) {
    return <ErrorState title="Missing workflow ID" message="The selected workflow route does not include an ID." />;
  }

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

      {workflowQuery.isLoading && <LoadingState title="Loading workflow" message="Reading the saved run and agent steps from the backend..." />}
      {workflowQuery.isError && <ErrorState title="Workflow not found" message="Could not load this workflow. It may have been deleted or the backend may be unavailable." />}

      {workflowQuery.data && (
        <div className="space-y-6">
          <Card
            title="Original Task"
            eyebrow="Request"
            actions={<StatusBadge status={workflowQuery.data.status} />}
          >
            <pre className="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm leading-7 text-slate-800">
              {formatWorkflowValue(getWorkflowTask(workflowQuery.data))}
            </pre>
          </Card>

          <WorkflowResultCard workflow={workflowQuery.data} title="Final Answer" eyebrow="Combined Output" />

          <WorkflowGraph workflow={workflowQuery.data} />

          {workflowQuery.data.error && (
            <ErrorState title="Workflow error" message={workflowQuery.data.error} />
          )}

          <div>
            <h3 className="text-xl font-semibold text-slate-950">Agent Steps</h3>
            <p className="mt-1 text-sm text-slate-500">
              Full execution detail for every specialized agent in the sequential workflow.
            </p>
          </div>

          <div className="space-y-5">
            {workflowQuery.data.steps.map((step, index) => (
              <AgentStepCard key={step.id} step={step} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
