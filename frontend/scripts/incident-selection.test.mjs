import test from "node:test";
import assert from "node:assert/strict";
import { activeAction, activePage } from "../src/incidentSelection.js";

test("selects the page that still needs a response", () => {
  assert.equal(activePage([{ id: "old", status: "acknowledged" }, { id: "current", status: "delivered" }]).id, "current");
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
