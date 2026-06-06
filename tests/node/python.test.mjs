import test from "node:test";
import assert from "node:assert/strict";
import { pythonCandidates } from "../../dist/node-cli/python.js";

test("python candidates prefer PYTHON env var", () => {
  const candidates = pythonCandidates({ PYTHON: "C:/Python312/python.exe" }, "linux");

  assert.equal(candidates[0].command, "C:/Python312/python.exe");
  assert.deepEqual(candidates[0].args, []);
  assert.equal(candidates[1].command, "python");
  assert.equal(candidates[2].command, "python3");
});

test("python candidates include Windows launcher fallbacks", () => {
  const candidates = pythonCandidates({}, "win32").map((candidate) => candidate.label);

  assert.ok(candidates.includes("python"));
  assert.ok(candidates.includes("python3"));
  assert.ok(candidates.includes("py -3.12"));
  assert.ok(candidates.includes("py -3"));
});
