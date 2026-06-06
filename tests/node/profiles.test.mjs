import { mkdtemp, writeFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import assert from "node:assert/strict";
import { loadProfile } from "../../dist/node-cli/profiles.js";

test("local-direct profile uses env port and bearer token", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "gads-profile-"));
  try {
    await writeFile(path.join(dir, ".env"), "PORT=9999\nMCP_BEARER_TOKEN=abc\n", "utf8");
    const profile = await loadProfile(dir, { profile: "local-direct" });
    assert.equal(profile.url, "http://localhost:9999/mcp");
    assert.equal(profile.token, "abc");
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test("brokered-readonly profile is reserved", async () => {
  await assert.rejects(
    () => loadProfile(process.cwd(), { profile: "brokered-readonly" }),
    /reserved/
  );
});
