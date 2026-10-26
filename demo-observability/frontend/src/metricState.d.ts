export function metricOutcome(before: number, current: number, direction: "higher" | "lower", state?: string): "blocked" | "steady" | "improved" | "regressed";
