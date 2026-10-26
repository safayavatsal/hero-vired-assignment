import test from "node:test";
import assert from "node:assert/strict";
import { metricOutcome } from "../src/metricState.js";

test("marks lower-is-better metrics as improved", () => {
  assert.equal(metricOutcome(3210, 850, "lower"), "improved");
});

test("does not claim improvement for an external dependency incident", () => {
  assert.equal(metricOutcome(22, 22, "higher", "external_dependency"), "blocked");
});
