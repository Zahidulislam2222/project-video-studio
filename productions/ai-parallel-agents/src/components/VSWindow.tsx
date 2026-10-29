import React from "react";
import { useCurrentFrame } from "remotion";
import { C, MONO, FONT } from "../theme";
import { typed, Caret } from "./ui";

export type Agent = "claude" | "codex";
export type Status = "idle" | "working" | "review" | "limit" | "switch" | "continue";

const agentColor = (a: Agent) => (a === "claude" ? C.claude : C.codex);
export const AgentMark: React.FC<{ agent: Agent; size?: number }> = ({ agent, size = 18 }) => (
  <span style={{ display: "inline-flex", alignItems: "center", gap: size * 0.4, color: agentColor(agent), fontFamily: MONO, fontWeight: 700, fontSize: size }}>
    <span style={{ fontSize: size * 1.1 }}>{agent === "claude" ? "✻" : "◆"}</span>
    {agent === "claude" ? "Claude Code" : "Codex"}
  </span>
);

const statusInfo: Record<Status, { text: string; color: string } | null> = {
  idle: null,
  working: { text: "working", color: C.cyan },
  review: { text: "ready for review", color: C.green },
  limit: { text: "usage limit reached", color: C.red },
  switch: { text: "switching provider", color: C.amber },
  continue: { text: "continuing task", color: C.green },
};

const codePalette = [C.violet, C.cyan, C.pink, C.amber, C.green, C.muted];

export const VSWindow: React.FC<{
  agent: Agent;
  width: number;
  height: number;
  seed?: number;
  label?: string;
  status?: Status;
  /** Frame (local) when code lines start writing. */
  writeAt?: number;
  lines?: { text: string; at: number; color?: string }[];
  focus?: number;
  showAgent?: boolean;
}> = ({ agent, width, height, seed = 0, label, status = "idle", writeAt = Infinity, lines = [], focus = 0, showAgent = true }) => {
  const frame = useCurrentFrame();
  const sc = width / 640;
  const titleH = 34 * sc;
  const termH = height * 0.36;
  const accent = agentColor(agent);
  const st = statusInfo[status];
  const nCode = 11;
  const written = isFinite(writeAt) ? Math.max(0, Math.min(nCode, Math.floor((frame - writeAt) / 9))) : 0;
  const glowColor = status === "limit" ? C.red : status === "review" || status === "continue" ? C.green : accent;
  const shake = status === "limit" ? Math.sin(frame * 2.1) * 2 * Math.max(0, 1 - ((frame % 60) / 20)) : 0;
  return (
    <div
      style={{
        width,
        height,
        borderRadius: 14 * sc,
        overflow: "hidden",
        background: "#0B0F1A",
        border: `${1.5 + focus * 1.5}px solid ${focus > 0.05 || status === "limit" ? glowColor : "#26324F"}`,
        boxShadow: `0 ${30 * sc}px ${70 * sc}px #000000AA, 0 0 ${10 + 60 * focus}px ${glowColor}${status === "limit" ? "88" : "44"}`,
        fontFamily: FONT,
        position: "relative",
        transform: `translateX(${shake}px)`,
      }}
    >
      {/* Title bar */}
      <div style={{ height: titleH, background: "#151B2B", display: "flex", alignItems: "center", padding: `0 ${12 * sc}px`, gap: 7 * sc, borderBottom: "1px solid #222B42" }}>
        {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => (
          <div key={c} style={{ width: 11 * sc, height: 11 * sc, borderRadius: 99, background: c }} />
        ))}
        <div style={{ flex: 1, display: "flex", justifyContent: "center" }}>
          <div style={{ fontSize: 14 * sc, color: C.muted, fontWeight: 600, letterSpacing: 0.4 }}>{label ?? ""}</div>
        </div>
        <div style={{ width: 40 * sc }} />
      </div>
      <div style={{ display: "flex", height: height - titleH - termH }}>
        {/* Activity bar */}
        <div style={{ width: 40 * sc, background: "#101524", display: "flex", flexDirection: "column", alignItems: "center", gap: 14 * sc, paddingTop: 14 * sc }}>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} style={{ width: 18 * sc, height: 18 * sc, borderRadius: 4 * sc, border: `2px solid ${i === 0 ? C.text : "#3A4566"}`, opacity: i === 0 ? 0.8 : 0.6 }} />
          ))}
        </div>
        {/* Explorer */}
        <div style={{ width: 120 * sc, background: "#0E1320", padding: 12 * sc, display: "flex", flexDirection: "column", gap: 9 * sc, borderRight: "1px solid #1C2438" }}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} style={{ height: 7 * sc, width: `${45 + ((i * 37 + seed * 13) % 50)}%`, marginLeft: (i % 3) * 10 * sc, borderRadius: 4, background: i === 2 + (seed % 3) ? accent + "AA" : "#2A3452" }} />
          ))}
        </div>
        {/* Editor */}
        <div style={{ flex: 1, padding: `${14 * sc}px ${16 * sc}px`, display: "flex", flexDirection: "column", gap: 9 * sc, position: "relative" }}>
          {Array.from({ length: nCode }).map((_, i) => {
            const base = i < 4 || i < 4 + written;
            const fresh = i >= 4 && i < 4 + written;
            const indent = ((i * 7 + seed) % 3) * 18 * sc;
            return (
              <div key={i} style={{ display: "flex", gap: 7 * sc, marginLeft: indent, opacity: base ? 1 : 0.08 }}>
                <div style={{ height: 8 * sc, width: (28 + ((i * 53 + seed * 7) % 60)) * sc, borderRadius: 4, background: codePalette[(i + seed) % codePalette.length] + (fresh ? "FF" : "AA") }} />
                <div style={{ height: 8 * sc, width: (40 + ((i * 31 + seed * 11) % 120)) * sc, borderRadius: 4, background: fresh ? C.text + "BB" : "#3A4566" }} />
                {i % 2 === 0 && <div style={{ height: 8 * sc, width: (20 + ((i * 17) % 50)) * sc, borderRadius: 4, background: codePalette[(i + seed + 2) % codePalette.length] + "99" }} />}
              </div>
            );
          })}
        </div>
      </div>
      {/* Terminal */}
      <div style={{ height: termH, background: "#080B13", borderTop: "1px solid #222B42", padding: `${10 * sc}px ${16 * sc}px`, fontFamily: MONO, fontSize: 15 * sc, color: C.text, overflow: "hidden" }}>
        <div style={{ display: "flex", gap: 18 * sc, fontSize: 11 * sc, color: C.dim, fontFamily: FONT, fontWeight: 700, letterSpacing: 1, marginBottom: 8 * sc }}>
          <span style={{ color: C.text, borderBottom: `2px solid ${accent}` }}>TERMINAL</span>
          <span>PROBLEMS</span>
          <span>OUTPUT</span>
        </div>
        {showAgent && (
          <div style={{ marginBottom: 6 * sc }}>
            <AgentMark agent={agent} size={15 * sc} />
          </div>
        )}
        {lines.map((l, i) => {
          const txt = typed(l.text, frame, l.at, 40);
          if (!txt) return null;
          const last = i === lines.length - 1 || frame < lines[i + 1].at;
          return (
            <div key={i} style={{ color: l.color ?? C.text, whiteSpace: "pre", lineHeight: 1.45 }}>
              {txt}
              {last && <Caret frame={frame} color={l.color ?? C.text} />}
            </div>
          );
        })}
      </div>
      {/* Status chip */}
      {st && (
        <div
          style={{
            position: "absolute",
            top: titleH + 10 * sc,
            right: 12 * sc,
            padding: `${5 * sc}px ${12 * sc}px`,
            borderRadius: 99,
            background: st.color + "22",
            border: `1.5px solid ${st.color}`,
            color: st.color,
            fontWeight: 700,
            fontSize: 14 * sc,
            display: "flex",
            alignItems: "center",
            gap: 8 * sc,
            boxShadow: `0 0 20px ${st.color}55`,
          }}
        >
          {status === "working" || status === "switch" ? (
            <div style={{ width: 12 * sc, height: 12 * sc, borderRadius: 99, border: `2px solid ${st.color}`, borderTopColor: "transparent", transform: `rotate(${frame * 14}deg)` }} />
          ) : (
            <div style={{ width: 9 * sc, height: 9 * sc, borderRadius: 99, background: st.color }} />
          )}
          {st.text}
        </div>
      )}
      {status === "limit" && <div style={{ position: "absolute", inset: 0, background: `repeating-linear-gradient(0deg, ${C.red}10 0 3px, transparent 3px 7px)` }} />}
    </div>
  );
};
