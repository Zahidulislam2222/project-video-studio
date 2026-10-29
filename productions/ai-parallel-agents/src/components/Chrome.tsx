import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "../theme";
import type { VideoData } from "../timing";

/** Chapter tag (top-left) and a chaptered progress bar along the top edge. */
export const Chrome: React.FC<{ data: VideoData; portrait: boolean }> = ({ data, portrait }) => {
  const frame = useCurrentFrame();
  const { fps, width, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const scene = data.scenes.find((s) => t >= s.start && t < s.end);
  const p = frame / durationInFrames;
  const local = scene ? (t - scene.start) * fps : 0;
  const tagIn = interpolate(local, [6, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const [num, name] = scene?.chapter ? scene.chapter.split(" · ") : ["", ""];
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 6, background: "#ffffff10" }}>
        <div style={{ width: `${p * 100}%`, height: "100%", background: `linear-gradient(90deg, ${C.cyan}, ${C.violet})`, boxShadow: `0 0 12px ${C.cyan}` }} />
        {data.scenes.slice(1).map((s) => (
          <div key={s.id} style={{ position: "absolute", left: (s.start / data.duration) * width, top: 0, width: 2, height: 6, background: C.bg }} />
        ))}
      </div>
      {scene?.chapter && (
        <div style={{ position: "absolute", top: portrait ? 90 : 46, left: portrait ? 60 : 64, display: "flex", alignItems: "center", gap: 16, opacity: tagIn, transform: `translateX(${(1 - tagIn) * -30}px)` }}>
          <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: portrait ? 30 : 24, color: C.cyan, padding: "6px 12px", border: `1.5px solid ${C.cyan}66`, borderRadius: 10, background: `${C.cyan}14` }}>{num}</div>
          <div style={{ width: 40 * tagIn, height: 2, background: C.cyan + "88" }} />
          <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: portrait ? 32 : 26, color: C.text, letterSpacing: 0.3 }}>{name}</div>
        </div>
      )}
    </AbsoluteFill>
  );
};
