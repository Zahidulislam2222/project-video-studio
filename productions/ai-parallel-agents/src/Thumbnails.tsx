import React from "react";
import { AbsoluteFill } from "remotion";
import "./theme";
import { C, FONT, MONO } from "./theme";
import { Background } from "./components/Background";
import { Orb3D } from "./components/Orb3D";
import { VSWindow, Agent, Status } from "./components/VSWindow";
import { IDoc, IShield, ICheck } from "./components/Icons";

const Big: React.FC<React.PropsWithChildren<{ size: number; color?: string; style?: React.CSSProperties }>> = ({ size, color = C.text, style, children }) => (
  <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 0.95, letterSpacing: -size * 0.035, color, textTransform: "uppercase", textShadow: "0 6px 0 #00000088, 0 0 40px #00000099", ...style }}>{children}</div>
);

const Tag: React.FC<React.PropsWithChildren<{ color: string; size?: number }>> = ({ color, size = 30, children }) => (
  <div style={{ display: "inline-flex", alignItems: "center", gap: 10, padding: `${size * 0.3}px ${size * 0.6}px`, borderRadius: 14, background: color, color: C.bg, fontFamily: FONT, fontWeight: 900, fontSize: size, textTransform: "uppercase", letterSpacing: 0.5, boxShadow: `0 0 30px ${color}88` }}>{children}</div>
);

const win = (a: Agent, w: number, status: Status, seed: number, label?: string) => (
  <VSWindow agent={a} width={w} height={w * 0.62} seed={seed} status={status} writeAt={-500} label={label} lines={[{ text: a === "claude" ? "$ claude" : "$ codex", at: -500, color: C.muted }]} focus={status === "limit" || status === "continue" ? 1 : 0.3} />
);

/** A: 4 projects, 1 developer */
export const ThumbA: React.FC = () => (
  <AbsoluteFill>
    <Background accent={C.cyan} accent2={C.violet} />
    <AbsoluteFill style={{ perspective: 1400 }}>
      <div style={{ position: "absolute", right: 40, top: 150, width: 640, height: 580, transform: "rotateY(-18deg) rotateX(6deg)", transformStyle: "preserve-3d" }}>
        {(["claude", "codex", "codex", "claude"] as Agent[]).map((a, i) => (
          <div key={i} style={{ position: "absolute", left: (i % 2) * 330, top: Math.floor(i / 2) * 215 + 60 }}>{win(a, 310, "working", i)}</div>
        ))}
      </div>
    </AbsoluteFill>
    <div style={{ position: "absolute", left: 56, top: 70 }}>
      <Big size={124} color={C.amber}>4 projects</Big>
      <Big size={150} style={{ marginTop: 6 }}>1 dev</Big>
      <div style={{ marginTop: 34, display: "flex", gap: 14 }}>
        <Tag color={C.claude}>Claude Code</Tag>
        <Tag color={C.codex}>Codex</Tag>
      </div>
      <div style={{ marginTop: 22, fontFamily: FONT, fontWeight: 800, fontSize: 40, color: C.text }}>at the same time</div>
    </div>
  </AbsoluteFill>
);

/** B: usage limit -> keep going */
export const ThumbB: React.FC = () => (
  <AbsoluteFill>
    <Background accent={C.red} accent2={C.green} />
    <div style={{ position: "absolute", left: 50, top: 60 }}>
      <Big size={120} color={C.red}>Limit hit?</Big>
      <Big size={120} color={C.green} style={{ marginTop: 10 }}>Keep going</Big>
    </div>
    <div style={{ position: "absolute", left: 60, bottom: 70, transform: "rotate(-4deg)" }}>{win("claude", 470, "limit", 2)}</div>
    <svg width={260} height={160} style={{ position: "absolute", left: 540, bottom: 150 }}>
      <defs>
        <linearGradient id="g" x1="0" x2="1">
          <stop offset="0" stopColor={C.red} />
          <stop offset="1" stopColor={C.green} />
        </linearGradient>
      </defs>
      <path d="M10 110 C 90 10, 170 10, 225 70" stroke="url(#g)" strokeWidth={18} fill="none" strokeLinecap="round" />
      <path d="M195 40 L 240 85 L 180 95 Z" fill={C.green} />
    </svg>
    <div style={{ position: "absolute", right: 50, bottom: 110, transform: "rotate(3deg)" }}>{win("codex", 470, "continue", 5)}</div>
    <div style={{ position: "absolute", right: 60, top: 70, display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 14 }}>
      <Tag color={C.violet} size={34}>OpenRouter</Tag>
      <Tag color={C.amber} size={34}>No lost context</Tag>
    </div>
  </AbsoluteFill>
);

/** C: /switch-provider skill */
export const ThumbC: React.FC = () => (
  <AbsoluteFill>
    <Background accent={C.cyan} accent2={C.violet} />
    <div style={{ position: "absolute", right: -40, top: 110, opacity: 0.95 }}>
      <Orb3D size={560} spin={0.5} />
    </div>
    <div style={{ position: "absolute", right: 170, top: 300, width: 220, height: 220, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 150, height: 150, borderRadius: 34, background: `${C.bg}EE`, border: `3px solid ${C.amber}`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 50px ${C.amber}88` }}>
        <IDoc size={92} color={C.amber} stroke={1.6} />
      </div>
    </div>
    <div style={{ position: "absolute", left: 56, top: 70 }}>
      <Big size={112}>Never lose</Big>
      <Big size={112} color={C.cyan} style={{ marginTop: 6 }}>context</Big>
      <div style={{ marginTop: 34, padding: "16px 26px", borderRadius: 18, background: "#05070FE6", border: `3px solid ${C.cyan}`, display: "inline-block", fontFamily: MONO, fontWeight: 700, fontSize: 64, color: C.text, boxShadow: `0 0 40px ${C.cyan}66` }}>
        <span style={{ color: C.cyan }}>/</span>switch-provider
      </div>
      <div style={{ marginTop: 30, display: "flex", gap: 12 }}>
        {[
          ["checkpoint", C.green],
          ["secret scan", C.pink],
          ["handoff", C.amber],
        ].map(([t, c]) => (
          <div key={t} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 16px", borderRadius: 12, border: `2.5px solid ${c}`, background: `${c}22`, color: C.text, fontFamily: FONT, fontWeight: 800, fontSize: 28 }}>
            {t === "secret scan" ? <IShield size={28} color={c as string} stroke={2.5} /> : <ICheck size={28} color={c as string} stroke={3} />}
            {t}
          </div>
        ))}
      </div>
    </div>
  </AbsoluteFill>
);

/** Shorts cover (1080x1920); key text kept inside the centre square for grid crops. */
export const ThumbShort: React.FC = () => (
  <AbsoluteFill>
    <Background accent={C.cyan} accent2={C.violet} />
    <div style={{ position: "absolute", left: 0, right: 0, top: 360, textAlign: "center" }}>
      <Big size={170} color={C.amber}>1 dev</Big>
      <Big size={150} style={{ marginTop: 10 }}>4 AI agents</Big>
    </div>
    <div style={{ position: "absolute", left: 60, right: 60, top: 790, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 26 }}>
      {(["claude", "codex", "codex", "claude"] as Agent[]).map((a, i) => (
        <div key={i}>{win(a, 467, i === 3 ? "limit" : "working", i)}</div>
      ))}
    </div>
    <div style={{ position: "absolute", left: 0, right: 0, top: 1450, display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
      <Big size={82} color={C.green}>Limit hit? Keep going</Big>
      <div style={{ display: "flex", gap: 14 }}>
        <Tag color={C.claude} size={34}>Claude Code</Tag>
        <Tag color={C.codex} size={34}>Codex</Tag>
      </div>
    </div>
  </AbsoluteFill>
);

