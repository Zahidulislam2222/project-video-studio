import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT } from "../theme";
import { useScene, useSpring, ease, first } from "../timing";
import { VSWindow, Agent, Status } from "../components/VSWindow";
import { IUser } from "../components/Icons";

const agents: Agent[] = ["claude", "codex", "claude", "codex"];
const tasks = ["› add login flow + tests", "› fix the checkout bug", "› write the API docs", "› refactor the dashboard"];

export const Setup: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait, word, sentence, variant } = useScene();
  const appear = variant === "long" ? sentence(0) : 0;
  const agentAt = first(word("agent"), word("claude"));
  // Focus cues: window one..four, or an automatic sweep in the short.
  const auto = first(word("task"), 40);
  const f = variant === "long" ? [word("one"), word("two"), word("three"), word("four")].map((x, i) => (isFinite(x) ? x : auto + i * 14)) : [0, 1, 2, 3].map((i) => auto + i * 12);
  const backAt = variant === "long" ? sentence(3) : Infinity;
  const cycleAt = variant === "long" ? sentence(4) : first(word("plan"), auto + 60);
  const cyc = useSpring(cycleAt);

  const ww = portrait ? 490 : 580;
  const wh = ww * 0.62;
  const gap = portrait ? 40 : 56;
  const gridW = ww * 2 + gap;
  const gridH = wh * 2 + gap;
  const gx = (width - gridW) / 2;
  const gy = portrait ? height * 0.42 - gridH / 2 : (height - gridH) / 2 - 30;

  let focusIdx = -1;
  for (let i = 0; i < 4; i++) if (frame >= f[i] - 4) focusIdx = i;
  if (frame >= backAt) focusIdx = 0;
  const tilt = Math.sin(frame / 90) * 3;

  return (
    <AbsoluteFill style={{ perspective: 2000 }}>
      <div style={{ position: "absolute", left: gx, top: gy, width: gridW, height: gridH, transformStyle: "preserve-3d", transform: `rotateX(${10 - cyc * 4}deg) rotateY(${tilt}deg) scale(${1 - cyc * 0.06})`, opacity: 1 - cyc * 0.55, filter: `blur(${cyc * 3}px)` }}>
        {agents.map((a, i) => {
          const col = i % 2;
          const row = Math.floor(i / 2);
          const s = useSpring(appear + i * 4);
          const focused = focusIdx === i && cyc < 0.5;
          let status: Status = "idle";
          if (frame >= f[i]) status = "working";
          if (i === 0 && frame >= backAt) status = "review";
          if (variant === "short" && frame >= f[i] + 40 && i % 2 === 0) status = "review";
          const lines = [
            { text: a === "claude" ? "$ claude" : "$ codex", at: agentAt + i * 5, color: C.muted },
            { text: tasks[i], at: f[i] + 2, color: a === "claude" ? C.claude : C.codex },
          ];
          return (
            <div key={i} style={{ position: "absolute", left: col * (ww + gap), top: row * (wh + gap), opacity: s, transform: `translateZ(${(1 - s) * -600 + (focused ? 40 : 0)}px) scale(${focused ? 1.03 : 1})` }}>
              <VSWindow agent={a} width={ww} height={wh} seed={i + 3} label={`window ${i + 1}`} status={status} writeAt={f[i] + 12} lines={lines} showAgent={frame >= agentAt} focus={focused ? 1 : 0} />
            </div>
          );
        })}
      </div>
      {/* the developer's cursor moving between windows */}
      {focusIdx >= 0 && cyc < 0.5 && (() => {
        const col = focusIdx % 2;
        const row = Math.floor(focusIdx / 2);
        const prev = Math.max(0, focusIdx - 1);
        const k = ease(frame, f[focusIdx] - 4, f[focusIdx] + 8);
        const tx = gx + col * (ww + gap) + ww * 0.5;
        const ty = gy + row * (wh + gap) + wh * 0.5;
        const px = gx + (prev % 2) * (ww + gap) + ww * 0.5;
        const py = gy + Math.floor(prev / 2) * (wh + gap) + wh * 0.5;
        const x = px + (tx - px) * k;
        const y = py + (ty - py) * k;
        return (
          <div style={{ position: "absolute", left: x - 34, top: y - 34, width: 68, height: 68, borderRadius: 99, background: `${C.bg}DD`, border: `2.5px solid ${C.text}`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 30px ${C.cyan}` }}>
            <IUser size={36} color={C.text} />
          </div>
        );
      })()}
      <Cycle at={cycleAt} portrait={portrait} />
    </AbsoluteFill>
  );
};

const steps = [
  { t: "Plan", c: C.violet, who: "you" },
  { t: "Build", c: C.cyan, who: "agent" },
  { t: "Review", c: C.amber, who: "you" },
  { t: "Next window", c: C.green, who: "you" },
];

const Cycle: React.FC<{ at: number; portrait: boolean }> = ({ at, portrait }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const s = useSpring(at);
  if (!isFinite(at) || frame < at) return null;
  const cx = width / 2;
  const cy = portrait ? height * 0.42 : height * 0.5;
  const r = portrait ? 300 : 280;
  const active = Math.floor((frame - at) / 22) % 4;
  return (
    <AbsoluteFill style={{ opacity: s }}>
      <svg width={width} height={height} style={{ position: "absolute" }}>
        <circle cx={cx} cy={cy} r={r} stroke="#ffffff22" strokeWidth={3} fill="none" />
        <circle cx={cx} cy={cy} r={r} stroke={C.cyan} strokeWidth={5} fill="none" strokeDasharray={`${2 * Math.PI * r * 0.18} ${2 * Math.PI * r}`} strokeDashoffset={-frame * 9} strokeLinecap="round" style={{ filter: `drop-shadow(0 0 8px ${C.cyan})` }} />
      </svg>
      <div style={{ position: "absolute", left: cx - 150, top: cy - 60, width: 300, textAlign: "center", fontFamily: FONT }}>
        <div style={{ fontSize: 26, color: C.muted, fontWeight: 600 }}>the agents build</div>
        <div style={{ fontSize: 40, color: C.text, fontWeight: 800 }}>you keep direction</div>
      </div>
      {steps.map((st, i) => {
        const ang = -Math.PI / 2 + (i * Math.PI) / 2;
        const x = cx + Math.cos(ang) * r;
        const y = cy + Math.sin(ang) * r;
        const on = active === i;
        const k = ease(frame, at + i * 6, at + i * 6 + 14);
        return (
          <div key={i} style={{ position: "absolute", left: x - 120, top: y - 44, width: 240, height: 88, borderRadius: 20, background: on ? `${st.c}33` : `${C.panel}F0`, border: `2px solid ${on ? st.c : st.c + "66"}`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", transform: `scale(${(0.6 + 0.4 * k) * (on ? 1.08 : 1)})`, opacity: k, boxShadow: on ? `0 0 40px ${st.c}77` : "none", fontFamily: FONT }}>
            <div style={{ fontSize: 32, fontWeight: 800, color: C.text }}>{st.t}</div>
            <div style={{ fontSize: 18, fontWeight: 600, color: st.c, letterSpacing: 1.5, textTransform: "uppercase" }}>{st.who}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
