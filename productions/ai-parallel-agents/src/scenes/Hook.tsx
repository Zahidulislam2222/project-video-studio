import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { C, FONT } from "../theme";
import { useScene, useSpring, ease, first } from "../timing";
import { VSWindow, Agent, Status } from "../components/VSWindow";
import { Orb3D } from "../components/Orb3D";
import { IUser } from "../components/Icons";
import { Title, Grad, Pill } from "../components/ui";

const agents: Agent[] = ["claude", "codex", "claude", "codex"];

export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait, word, sentence, length, variant } = useScene();
  const devAt = Math.max(0, word("developer") - 14);
  const winAt = first(word("four", 0), 30);
  const agentsAt = word("agents");
  const badgeAt = first(word("claude"), word("agents"));
  const limitAt = word("limit");
  const switchAt = first(word("switches"), word("stops"));
  const titleAt = variant === "long" ? sentence(4) : Infinity;

  const dev = useSpring(devAt);
  const titleS = useSpring(titleAt);
  const cx = width / 2;
  const cy = portrait ? height * 0.43 : height * 0.47;
  const rx = portrait ? width * 0.25 : width * 0.3;
  const ry = portrait ? height * 0.22 : height * 0.27;
  const ww = portrait ? 470 : 470;
  const wh = ww * 0.64;
  const pullBack = ease(frame, titleAt, titleAt + 25);
  const orbit = frame * 0.004;

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ perspective: 1600, transform: `scale(${1 - pullBack * 0.18})`, opacity: 1 - pullBack * 0.75, filter: `blur(${pullBack * 6}px)` }}>
        {/* connection lines */}
        <svg width={width} height={height} style={{ position: "absolute" }}>
          {agents.map((_, i) => {
            const ang = -Math.PI * 0.75 + i * (Math.PI / 2) + Math.sin(orbit) * 0.05;
            const x = cx + Math.cos(ang) * rx;
            const y = cy + Math.sin(ang) * ry;
            const p = ease(frame, winAt + i * 5 + 10, winAt + i * 5 + 35);
            return (
              <line key={i} x1={cx} y1={cy} x2={cx + (x - cx) * p} y2={cy + (y - cy) * p} stroke={i % 2 ? C.codex : C.claude} strokeWidth={2.5} strokeDasharray="8 10" strokeDashoffset={-frame * 1.5} opacity={0.7} />
            );
          })}
        </svg>
        {agents.map((a, i) => {
          const ang = -Math.PI * 0.75 + i * (Math.PI / 2) + Math.sin(orbit) * 0.05;
          const x = cx + Math.cos(ang) * rx;
          const y = cy + Math.sin(ang) * ry;
          const s = useSpring(winAt + i * 5);
          let status: Status = frame > first(agentsAt, winAt + 30) ? "working" : "idle";
          if (i === 2 && frame > limitAt) status = "limit";
          if (i === 2 && frame > switchAt) status = "switch";
          if (i === 2 && frame > switchAt + 26) status = "continue";
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x - ww / 2,
                top: y - wh / 2,
                transform: `translateZ(${(1 - s) * -900}px) rotateY(${(Math.cos(ang) > 0 ? -1 : 1) * 14}deg) rotateX(${(Math.sin(ang) > 0 ? 1 : -1) * 6}deg)`,
                opacity: s,
              }}
            >
              <VSWindow agent={a} width={ww} height={wh} seed={i} status={status} writeAt={first(agentsAt, winAt + 30) + i * 6} showAgent={frame > badgeAt} focus={i === 2 && frame > limitAt ? 1 : 0} />
            </div>
          );
        })}
        {/* developer core */}
        <div style={{ position: "absolute", left: cx - 190, top: cy - 190, width: 380, height: 380, transform: `scale(${dev})`, opacity: dev }}>
          <Orb3D size={380} spin={0.8} />
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 110, height: 110, borderRadius: 99, background: `${C.bg}EE`, border: `2px solid ${C.cyan}`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 40px ${C.cyan}88` }}>
              <IUser size={58} color={C.text} />
            </div>
          </div>
        </div>
        {/* counters */}
        <div style={{ position: "absolute", left: 0, right: 0, top: portrait ? height * 0.1 : 44, display: "flex", justifyContent: "center", gap: 18, opacity: ease(frame, winAt, winAt + 12) }}>
          <Pill color={C.cyan}>1 developer</Pill>
          <Pill color={C.violet}>4 projects</Pill>
          <Pill color={C.amber} style={{ opacity: ease(frame, agentsAt, agentsAt + 10) }}>4 AI agents</Pill>
        </div>
      </AbsoluteFill>
      {isFinite(titleAt) && (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", gap: 30, opacity: titleS }}>
          <Title size={portrait ? 88 : 104} style={{ textAlign: "center", transform: `translateY(${(1 - titleS) * 40}px)` }}>
            Parallel projects
            <br />
            <Grad>with AI agents</Grad>
          </Title>
          <div style={{ fontFamily: FONT, fontSize: 34, color: C.muted, fontWeight: 500, opacity: ease(frame, titleAt + 12, titleAt + 30) }}>Claude Code · Codex · OpenRouter · switch-provider</div>
        </AbsoluteFill>
      )}
      <div style={{ display: "none" }}>{interpolate(length, [0, 1], [0, 1])}</div>
    </AbsoluteFill>
  );
};
