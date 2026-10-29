// Render thumbnails as full-resolution PNGs: node tools/thumbs.mjs <outDir>
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";

const outDir = process.argv[2] ?? "out";
const browserExecutable = process.env.REMOTION_BROWSER || "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
for (const [id, file] of [["ThumbA", "thumbnail-long-A.png"], ["ThumbB", "thumbnail-long-B.png"], ["ThumbC", "thumbnail-long-C.png"], ["ThumbShort", "thumbnail-short.png"]]) {
  const composition = await selectComposition({ serveUrl, id, browserExecutable, chromiumOptions: { gl: "swangle" } });
  await renderStill({ serveUrl, composition, frame: 0, output: `${outDir}/${file}`, browserExecutable, chromiumOptions: { gl: "swangle" }, imageFormat: "png" });
  console.log("thumb", file);
}
