import React, { useMemo } from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT } from "../theme";
import type { VideoData, Word } from "../timing";

type Group = { words: Word[]; s: number; e: number };

const buildGroups = (data: VideoData, maxWords: number, maxChars: number): Group[] => {
  const groups: Group[] = [];
  for (const sc of data.scenes)
    for (const se of sc.sentences) {
      let cur: Word[] = [];
      const flush = () => {
        if (cur.length) groups.push({ words: cur, s: cur[0].s, e: cur[cur.length - 1].e });
        cur = [];
      };
      se.words.forEach((w, i) => {
        const chars = cur.reduce((a, x) => a + x.w.length + 1, 0) + w.w.length;
        if (cur.length >= maxWords || chars > maxChars) flush();
        cur.push(w);
        const next = se.words[i + 1];
        if (/[.?!:;]$/.test(w.w) || (/,$/.test(w.w) && cur.length >= 2 && next)) flush();
      });
      flush();
    }
  // Hold each group until the next starts (max 0.6s), so captions don't flicker.
  for (let i = 0; i < groups.length; i++) {
    const next = groups[i + 1];
    groups[i].e = Math.min(groups[i].e + 0.6, next ? next.s - 0.02 : groups[i].e + 0.6);
  }
  return groups;
};

export const Captions: React.FC<{ data: VideoData; portrait: boolean }> = ({ data, portrait }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const t = frame / fps;
  const groups = useMemo(() => buildGroups(data, portrait ? 4 : 7, portrait ? 26 : 44), [data, portrait]);
  const g = groups.find((x) => t >= x.s - 0.08 && t <= x.e);
  if (!g) return null;
  const local = frame - Math.round((g.s - 0.08) * fps);
  const pop = spring({ frame: local, fps, config: { damping: 14, stiffness: 180, mass: 0.6 } });
  const size = portrait ? 64 : 50;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: portrait ? height * 0.17 : 64, pointerEvents: "none" }}>
      <div
        style={{
          transform: `translateY(${(1 - pop) * 24}px) scale(${0.92 + pop * 0.08})`,
          opacity: pop,
          padding: portrait ? "18px 30px" : "14px 30px",
          borderRadius: 22,
          background: "#05070FCC",
          border: `1.5px solid #ffffff14`,
          boxShadow: "0 20px 50px #00000080",
          maxWidth: portrait ? "88%" : "80%",
          textAlign: "center",
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          columnGap: size * 0.28,
          rowGap: 4,
        }}
      >
        {g.words.map((w, i) => {
          const active = t >= w.s && t < w.e + 0.04;
          const spoken = t >= w.e;
          const k = Math.max(0, Math.min(1, (t - w.s) / 0.12));
          return (
            <span
              key={i}
              style={{
                fontFamily: FONT,
                fontWeight: 800,
                fontSize: size,
                lineHeight: 1.18,
                letterSpacing: -0.5,
                color: active ? C.amber : spoken ? C.text : "#ffffff70",
                textShadow: active ? `0 0 24px ${C.amber}88` : "0 2px 8px #000",
                transform: `translateY(${active ? -3 * k : 0}px) scale(${active ? 1 + 0.06 * k : 1})`,
                display: "inline-block",
              }}
            >
              {w.w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
