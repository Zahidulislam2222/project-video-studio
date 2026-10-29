// Render review stills: node tools/stills.mjs <CompositionId> <outDir> <sec> [sec...]
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";

const [id, outDir, ...secs] = process.argv.slice(2);
const browserExecutable = process.env.REMOTION_BROWSER || "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const composition = await selectComposition({ serveUrl, id, browserExecutable, chromiumOptions: { gl: "swangle" } });
for (const s of secs) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round(Number(s) * 30));
  await renderStill({ serveUrl, composition, frame, output: `${outDir}/${id}-${s}.png`, browserExecutable, chromiumOptions: { gl: "swangle" }, scale: 0.5 });
  console.log("still", s);
}
