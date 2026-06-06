import test from "node:test";
import assert from "node:assert/strict";
import { parseEnv, valueLooksMissing } from "../../dist/node-cli/env.js";
import { generateBearerToken } from "../../dist/node-cli/setup.js";

test("parseEnv reads simple env files without comments", () => {
  const values = parseEnv("# comment\nA=1\nB=\"two=2\"\nEMPTY=\n");
  assert.deepEqual(values, { A: "1", B: "two=2", EMPTY: "" });
});

test("placeholder detection catches setup placeholders", () => {
  assert.equal(valueLooksMissing("replace-with-long-random-token"), true);
  assert.equal(valueLooksMissing("YOUR_TOKEN"), true);
  assert.equal(valueLooksMissing("real-token-value"), false);
});

test("generated bearer token is url-safe and long", () => {
  const token = generateBearerToken();
  assert.ok(token.length >= 40);
  assert.match(token, /^[A-Za-z0-9_-]+$/);
});
