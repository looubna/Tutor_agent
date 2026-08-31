import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    /**
     * The repo root, not `apps/web`. `data/words.de.json` — the hand-checked
     * German word file the exercise rules are computed from — is shared with
     * the scripts and, later, the agent service, so it lives above this app.
     * Without this, Turbopack refuses to resolve the `@data/*` alias out of
     * its own directory. `tsc` resolves it either way, so the error only shows
     * up at build time.
     */
    root: path.join(import.meta.dirname, "..", ".."),
  },
};

export default nextConfig;
