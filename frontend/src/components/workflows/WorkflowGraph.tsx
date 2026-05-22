import { useEffect, useMemo, useState } from 'react';
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  type Edge,
  type Node,
  ReactFlow,
  type NodeMouseHandler,
  type NodeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Card } from '../ui/Card';
import { StatusBadge } from '../ui/StatusBadge';
import type { AgentRole, WorkflowRun, WorkflowStatus, WorkflowStep } from '../../types/workflow';
import { formatDuration, formatWorkflowValue, getStepTitle, roleLabels } from '../../lib/workflowDisplay';

const agentOrder: AgentRole[] = [
  'planner',
  'researcher',
  'technical_architect',
  'developer',
  'reviewer',
  'final_answer',
];

const roleDescriptions: Record<AgentRole, string> = {
  planner: 'Breaks the request into smaller tasks.',
  researcher: 'Adds useful context and background.',
  technical_architect: 'Proposes architecture and technology choices.',
  developer: 'Turns the plan into implementation guidance.',
  reviewer: 'Checks quality, risks, and missing details.',
  final_answer: 'Combines the previous outputs into one answer.',
};

const nodeStatusClasses: Record<WorkflowStatus, string> = {
  pending: 'border-amber-200 bg-amber-50 text-amber-950 shadow-amber-100',
  running: 'border-blue-200 bg-blue-50 text-blue-950 shadow-blue-100',
  completed: 'border-emerald-200 bg-emerald-50 text-emerald-950 shadow-emerald-100',
  failed: 'border-rose-200 bg-rose-50 text-rose-950 shadow-rose-100',
};

const minimapStatusColors: Record<WorkflowStatus, string> = {
  pending: '#fef3c7',
  running: '#dbeafe',
  completed: '#d1fae5',
  failed: '#ffe4e6',
};

interface WorkflowAgentNodeData extends Record<string, unknown> {
  role: AgentRole;
  title: string;
  status: WorkflowStatus;
  durationMs?: number | null;
}

type WorkflowAgentNode = Node<WorkflowAgentNodeData, 'workflowAgent'>;

function WorkflowAgentNode({ data }: NodeProps<WorkflowAgentNode>) {
  return (
    <div
      className={`w-52 rounded-2xl border px-4 py-3 shadow-sm transition ${nodeStatusClasses[data.status]}`}
    >
      <Handle type="target" position={Position.Left} className="!h-2.5 !w-2.5 !border-2 !border-white !bg-slate-400" />
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            {data.role.replace('_', ' ')}
          </p>
          <p className="mt-1 text-sm font-semibold text-slate-950">{data.title}</p>
        </div>
        <StatusBadge status={data.status} />
      </div>
      <p className="mt-3 text-xs font-medium text-slate-500">Duration: {formatDuration(data.durationMs)}</p>
      <Handle type="source" position={Position.Right} className="!h-2.5 !w-2.5 !border-2 !border-white !bg-slate-400" />
    </div>
  );
}

const nodeTypes = {
  workflowAgent: WorkflowAgentNode,
};

interface WorkflowGraphProps {
  workflow: WorkflowRun;
}

function findStepForRole(steps: WorkflowStep[], role: AgentRole): WorkflowStep | undefined {
  return steps.find((step) => step.role === role);
}

function getInitialSelectedRole(workflow: WorkflowRun): AgentRole {
  const failedStep = workflow.steps.find((step) => step.status === 'failed');
  if (failedStep) {
    return failedStep.role;
  }

  const finalStep = workflow.steps.find((step) => step.role === 'final_answer');
  if (finalStep) {
    return finalStep.role;
  }

  return workflow.steps[0]?.role ?? 'planner';
}

export function WorkflowGraph({ workflow }: WorkflowGraphProps) {
  const [selectedRole, setSelectedRole] = useState<AgentRole>(() => getInitialSelectedRole(workflow));

  useEffect(() => {
    setSelectedRole(getInitialSelectedRole(workflow));
  }, [workflow.id]);

  const stepsByRole = useMemo(() => {
    return agentOrder.reduce<Record<AgentRole, WorkflowStep | undefined>>((accumulator, role) => {
      accumulator[role] = findStepForRole(workflow.steps, role);
      return accumulator;
    }, {} as Record<AgentRole, WorkflowStep | undefined>);
  }, [workflow.steps]);

  const nodes = useMemo<WorkflowAgentNode[]>(() => {
    return agentOrder.map((role, index) => {
      const step = stepsByRole[role];
      return {
        id: role,
        type: 'workflowAgent',
        position: { x: index * 260, y: index % 2 === 0 ? 40 : 130 },
        data: {
          role,
          title: step ? getStepTitle(step) : roleLabels[role],
          status: step?.status ?? 'pending',
          durationMs: step?.duration_ms,
        },
      };
    });
  }, [stepsByRole]);

  const edges = useMemo<Edge[]>(() => {
    return agentOrder.slice(0, -1).map((role, index) => ({
      id: `${role}-${agentOrder[index + 1]}`,
      source: role,
      target: agentOrder[index + 1],
      animated: stepsByRole[role]?.status === 'running' || stepsByRole[agentOrder[index + 1]]?.status === 'running',
      className: 'stroke-slate-300',
    }));
  }, [stepsByRole]);

  const handleNodeClick: NodeMouseHandler<WorkflowAgentNode> = (_, node) => {
    setSelectedRole(node.id as AgentRole);
  };

  const selectedStep = stepsByRole[selectedRole];
  const selectedStatus = selectedStep?.status ?? 'pending';

  return (
    <Card title="Workflow Graph" eyebrow="Visualization" actions={<StatusBadge status={workflow.status} />}>
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="min-h-[420px] overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.35}
            maxZoom={1.4}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable
            onNodeClick={handleNodeClick}
            className="bg-slate-50"
          >
            <Background gap={20} size={1} color="#cbd5e1" />
            <Controls showInteractive={false} />
            <MiniMap
              pannable
              zoomable
              nodeColor={(node) => minimapStatusColors[(node.data as unknown as WorkflowAgentNodeData).status]}
              maskColor="rgba(241, 245, 249, 0.7)"
            />
          </ReactFlow>
        </div>

        <aside className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Selected Agent</p>
              <h3 className="mt-1 text-lg font-semibold text-slate-950">
                {selectedStep ? getStepTitle(selectedStep) : roleLabels[selectedRole]}
              </h3>
              <p className="mt-1 text-sm text-slate-500">{roleDescriptions[selectedRole]}</p>
            </div>
            <StatusBadge status={selectedStatus} />
          </div>

          <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-2xl bg-slate-50 p-3">
              <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Role</dt>
              <dd className="mt-1 font-medium capitalize text-slate-900">{selectedRole.replace('_', ' ')}</dd>
            </div>
            <div className="rounded-2xl bg-slate-50 p-3">
              <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Duration</dt>
              <dd className="mt-1 font-medium text-slate-900">{formatDuration(selectedStep?.duration_ms)}</dd>
            </div>
          </dl>

          <div className="mt-5 space-y-4">
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Input</h4>
              <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs leading-5 text-slate-700">
                {selectedStep ? formatWorkflowValue(selectedStep.input) : 'This agent did not run yet.'}
              </pre>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Output</h4>
              <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap rounded-2xl border border-slate-200 bg-white p-4 text-xs leading-5 text-slate-800">
                {selectedStep ? formatWorkflowValue(selectedStep.output) : 'No output yet.'}
              </pre>
            </div>
            {selectedStep?.error && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                <p className="font-semibold">Error</p>
                <p className="mt-1 whitespace-pre-wrap">{selectedStep.error}</p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </Card>
  );
}
