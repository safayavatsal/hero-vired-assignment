export function metricOutcome(before, current, direction, state = "degraded") {
  if (state === "external_dependency") return "blocked";
  if (before === current) return "steady";
  const improved = direction === "higher" ? current > before : current < before;
  return improved ? "improved" : "regressed";
}
