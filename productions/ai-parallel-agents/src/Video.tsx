import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import "./theme";
import { C } from "./theme";
import { SceneProvider, VideoData } from "./timing";
import { Background } from "./components/Background";
import { Captions } from "./components/Captions";
import { Chrome } from "./components/Chrome";
import { Hook } from "./scenes/Hook";
import { Shift } from "./scenes/Shift";
import { Setup } from "./scenes/Setup";
import { Docs } from "./scenes/Docs";
import { Limit } from "./scenes/Limit";
import { Skill } from "./scenes/Skill";
import { Menu } from "./scenes/Menu";
import { Resume } from "./scenes/Resume";
import { Recap } from "./scenes/Recap";
import { Outro } from "./scenes/Outro";

export const OUTRO_HOLD = 90;
const OVERLAP = 10;

const scenes: Record<string, { C: React.FC; a: string; b: string }> = {
  hook: { C: Hook, a: C.cyan, b: C.violet },
  shift: { C: Shift, a: C.violet, b: C.cyan },
  setup: { C: Setup, a: C.claude, b: C.codex },
  docs: { C: Docs, a: C.violet, b: C.pink },
  limit: { C: Limit, a: C.red, b: C.amber },
  skill: { C: Skill, a: C.cyan, b: C.violet },
  menu: { C: Menu, a: C.violet, b: C.amber },
  resume: { C: Resume, a: C.green, b: C.cyan },
  recap: { C: Recap, a: C.cyan, b: C.green },
  outro: { C: Outro, a: C.cyan, b: C.violet },
};

const Shell: React.FC<React.PropsWithChildren<{ dur: number; last: boolean }>> = ({ dur, last, children }) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exit = last ? 0 : interpolate(frame, [dur - OVERLAP, dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const zoom = 1 + (frame / Math.max(1, dur)) * 0.025;
  return (
    <AbsoluteFill
      style={{
        opacity: enter * (1 - exit),
        transform: `scale(${zoom * (1.04 - 0.04 * enter) * (1 + exit * 0.06)})`,
        filter: enter < 1 || exit > 0 ? `blur(${(1 - enter) * 10 + exit * 10}px)` : undefined,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

export const Video: React.FC<{ data: VideoData; portrait: boolean; audio: string }> = ({ data, portrait, audio }) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();
  const t = frame / fps;
  const cur = data.scenes.find((s) => t >= s.start && t < s.end) ?? data.scenes[data.scenes.length - 1];
  const variant = data.id === "long" ? "long" : "short";
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Background accent={scenes[cur.id].a} accent2={scenes[cur.id].b} />
      {data.scenes.map((s, i) => {
        const from = Math.round(s.start * fps);
        const last = i === data.scenes.length - 1;
        const dur = last ? durationInFrames - from : Math.round(s.end * fps) - from + OVERLAP;
        const Comp = scenes[s.id].C;
        return (
          <Sequence key={s.id} from={from} durationInFrames={dur} name={s.id}>
            <SceneProvider value={{ scene: s, portrait, variant }}>
              <Shell dur={dur} last={last}>
                <Comp />
              </Shell>
            </SceneProvider>
          </Sequence>
        );
      })}
      <Chrome data={data} portrait={portrait} />
      <Captions data={data} portrait={portrait} />
      <Audio src={staticFile(audio)} />
    </AbsoluteFill>
  );
};
