import test from "node:test";
import assert from "node:assert/strict";
import { activeAction, activePage, scenarioForService, workflowStates } from "../src/lib/incidentSelection.js";

test("selects a scenario from the service returned by the API", () => {
  assert.equal(scenarioForService([
    { id: "cache_stampede", service: "catalog-api" },
    { id: "disk_pressure", service: "orders-worker" },
  ], "catalog-api"), "cache_stampede");
});

test("selects the page that still needs a response", () => {
  assert.equal(activePage([{ id: "old", status: "acknowledged" }, { id: "current", status: "delivered" }]).id, "current");
});

test("keeps the newest page after acknowledgement", () => {
  assert.equal(activePage([{ id: "old", status: "delivered" }, { id: "current", status: "acknowledged" }]).id, "current");
});

test("selects the latest action proposal", () => {
  assert.equal(activeAction([{ id: "old", status: "verified" }, { id: "current", status: "pending_approval" }]).id, "current");
});

test("ignores action proposals for another scenario or service", () => {
  assert.equal(activeAction([
    { id: "stale", scenario_id: "deployment_regression", target: "payments-api" },
    { id: "current", scenario_id: "disk_pressure", target: "orders-worker" },
  ], { scenarioId: "disk_pressure", target: "orders-worker" }).id, "current");
});

test("keeps the workflow sequential until each operator decision is complete", () => {
  assert.deepEqual(workflowStates(null, null, null), {
    investigation: "current",
    response: "locked",
    action: "locked",
  });
  assert.deepEqual(workflowStates({ status: "completed", findings: [{}] }, { status: "acknowledged" }, { status: "pending_approval" }), {
    investigation: "done",
    response: "done",
    action: "current",
  });
  assert.equal(workflowStates({ status: "completed", findings: [{}] }, { status: "replied" }, { status: "verified" }).response, "current");
  assert.equal(workflowStates({ status: "completed", findings: [{}] }, { status: "replied" }, { status: "verified" }).action, "locked");
  assert.equal(workflowStates({ status: "completed", findings: [{}] }, { status: "acknowledged" }, undefined, true).action, "done");
});
