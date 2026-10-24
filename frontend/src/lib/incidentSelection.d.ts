type WorkflowItem = { id: string; status: string; scenario_id?: string; target?: string };

export function activePage<T extends WorkflowItem>(pages: T[]): T | undefined;
export function activeAction<T extends WorkflowItem>(actions: T[], match?: { scenarioId: string; target: string }): T | undefined;
export function workflowStates(investigation: { status?: string; findings?: unknown[] } | null, page: WorkflowItem | undefined, action: WorkflowItem | undefined, noLocalAction?: boolean): { investigation: string; response: string; action: string };
