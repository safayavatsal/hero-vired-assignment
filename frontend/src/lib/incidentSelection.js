export function activePage(pages) {
  return pages[pages.length - 1];
}

export function activeAction(actions, match) {
  const eligible = match
    ? actions.filter((action) => action.scenario_id === match.scenarioId && action.target === match.target)
    : actions;
  return eligible[eligible.length - 1];
}

export function workflowStates(investigation, page, action, noLocalAction = false) {
  const findingReady = Boolean(investigation && (investigation.status === "completed" || investigation.findings?.length));
  const responderAcknowledged = page?.status === "acknowledged" || page?.status === "replied";
  const actionVerified = action?.status === "verified" || (noLocalAction && responderAcknowledged);

  return {
    investigation: findingReady ? "done" : "current",
    response: !findingReady ? "locked" : responderAcknowledged ? "done" : "current",
    action: !responderAcknowledged ? "locked" : actionVerified ? "done" : "current",
  };
}
