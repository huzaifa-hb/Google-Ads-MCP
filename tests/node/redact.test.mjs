import test from "node:test";
import assert from "node:assert/strict";
import { redactText, redactValue } from "../../dist/node-cli/redact.js";

test("redactValue hides sensitive env names", () => {
  assert.equal(redactValue("MCP_BEARER_TOKEN", "abc123"), "[REDACTED]");
  assert.equal(redactValue("PORT", "8080"), "8080");
});

test("redactText hides bearer and URL query tokens", () => {
  const text = redactText("Authorization: Bearer abc123 gptToken=secret-value");
  assert.equal(text, "Authorization: Bearer [REDACTED] gptToken=[REDACTED]");
});
