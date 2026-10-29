import React from "react";
import { C, FONT, MONO } from "../theme";

export const Pill: React.FC<React.PropsWithChildren<{ color?: string; style?: React.CSSProperties; mono?: boolean; size?: number }>> = ({ color = C.cyan, style, children, mono, size = 22 }) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      padding: `${size * 0.36}px ${size * 0.8}px`,
      borderRadius: 999,
      border: `1.5px solid ${color}66`,
      background: `${color}1A`,
      color,
      fontFamily: mono ? MONO : FONT,
      fontWeight: 600,
      fontSize: size,
      letterSpacing: mono ? 0 : 0.2,
      whiteSpace: "nowrap",
      boxShadow: `0 0 24px ${color}22`,
      ...style,
    }}
  >
    {children}
  </div>
);

export const Glass: React.FC<React.PropsWithChildren<{ style?: React.CSSProperties; glow?: string }>> = ({ style, children, glow }) => (
  <div
    style={{
      background: `linear-gradient(160deg, ${C.panel2}F2, ${C.panel}F2)`,
      border: `1.5px solid ${glow ? glow + "88" : C.line}`,
      borderRadius: 22,
      boxShadow: `0 30px 80px #00000099, inset 0 1px 0 #ffffff10${glow ? `, 0 0 50px ${glow}33` : ""}`,
      ...style,
    }}
  >
    {children}
  </div>
);

export const Title: React.FC<React.PropsWithChildren<{ size?: number; style?: React.CSSProperties }>> = ({ size = 72, style, children }) => (
  <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: size, color: C.text, letterSpacing: -size * 0.025, lineHeight: 1.05, ...style }}>{children}</div>
);

export const Grad: React.FC<React.PropsWithChildren<{ a?: string; b?: string }>> = ({ a = C.cyan, b = C.violet, children }) => (
  <span style={{ background: `linear-gradient(90deg, ${a}, ${b})`, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>{children}</span>
);

/** Typewriter: reveals `text` from frame `at` at `cps` characters/second. */
export const typed = (text: string, frame: number, at: number, cps = 32, fps = 30) => {
  if (!isFinite(at) || frame < at) return "";
  const n = Math.floor(((frame - at) / fps) * cps);
  return text.slice(0, n);
};

export const Caret: React.FC<{ frame: number; color?: string }> = ({ frame, color = C.text }) => (
  <span style={{ display: "inline-block", width: "0.55em", height: "1.05em", background: color, verticalAlign: "-0.15em", opacity: Math.floor(frame / 15) % 2 ? 0.15 : 0.9, marginLeft: 2 }} />
);
