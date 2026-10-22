type WorkflowItem = { id: string; status: string; scenario_id?: string; target?: string };

export function activePage<T extends WorkflowItem>(pages: T[]): T | undefined;
export function activeAction<T extends WorkflowItem>(actions: T[], match?: { scenarioId: string; target: string }): T | undefined;
