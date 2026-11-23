// Starts the collect workflow every 15 minutes (Cloudflare Worker with a Cron Trigger).
//
// Why it exists: GitHub's own schedule created about 3.5 runs a day for this repository
// (35 in 10 days, at random minutes), while a manual "Run workflow" starts within a second.
// This does the same thing as that button, on time.
//
// GITHUB_TOKEN is a Worker secret: a fine-grained token for this repository only, with one
// permission, "Actions: write". It can start or cancel workflow runs here, nothing else.
const DISPATCH_URL =
  "https://api.github.com/repos/valentin-shch/live-bike-monitor/actions/workflows/collect.yml/dispatches";

export default {
  async scheduled(controller, env) {
    const response = await fetch(DISPATCH_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "live-bike-monitor-trigger", // GitHub rejects API calls without one
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "main" }),
    });
    if (!response.ok) {
      // Fails the invocation so it shows as an error in the Worker's logs. The token never
      // appears here: only the status and GitHub's message are kept.
      throw new Error(`dispatch failed: ${response.status} ${(await response.text()).slice(0, 200)}`);
    }
  },
};
