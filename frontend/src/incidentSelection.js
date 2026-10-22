export function activePage(pages) {
  return pages.find((page) => page.status === "delivered") ?? pages[pages.length - 1];
}

export function activeAction(actions, match) {
  const eligible = match
    ? actions.filter((action) => action.scenario_id === match.scenarioId && action.target === match.target)
    : actions;
  return eligible[eligible.length - 1];
}
