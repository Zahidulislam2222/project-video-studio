import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO, docColors } from "../theme";
import { useScene, useSpring, ease, first } from "../timing";
import { Orb3D } from "../components/Orb3D";
import { Pill } from "../components/ui";
import { ITarget, ILayers, IPalette, IBrain, IRules, IList, ICpu } from "../components/Icons";

const docs = [
  { k: "requirements", t: "Requirements", d: "what & why", I: ITarget, f: "PRD" },
  { k: "architecture", t: "Architecture", d: "stack · structure · data flow", I: ILayers, f: "dossier" },
  { k: "design", t: "Design", d: "colors · type · components", I: IPalette, f: "DESIGN.md" },
  { k: "memory", t: "Memory", d: "current state · next steps", I: IBrain, f: "memory/" },
  { k: "rules", t: "Rules", d: "commands · conventions", I: IRules, f: "CLAUDE.md · AGENTS.md" },
  { k: "tracker", t: "Tracker", d: "tasks · status · evidence", I: IList, f: "TASKS.md" },
];

export const Docs: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait, word, sentence, variant } = useScene();
  const guessAt = variant === "long" ? sentence(0) : Infinity;
  const cues = docs.map((d) => word(d.k));
  const readAt = variant === "long" ? sentence(8) : first(word("decisions"), cues[5] + 30);
  const winAt = variant === "long" ? sentence(9) : Infinity;
  const orbS = useSpring(0);
  const cx = width / 2;
  const cy = portrait ? height * 0.25 : height * 0.47;
  const orbSize = portrait ? 420 : 460;
  const cardsIn = Math.min(...cues);
  const guessFade = 1 - ease(frame, cardsIn - 10, cardsIn + 10);

  const pos = (i: number) => {
    if (portrait) {
      const cw = 450, ch = 168;
      const col = i % 2, row = Math.floor(i / 2);
      return { x: width / 2 - cw - 14 + col * (cw + 28), y: height * 0.45 + row * (ch + 28), w: cw, h: ch };
    }
    const cw = 470, ch = 170;
    const left = i < 3;
    const row = i % 3;
    return { x: left ? 130 : width - 130 - cw, y: 205 + row * (ch + 36), w: cw, h: ch };
  };
  const reading = frame >= readAt;

  return (
    <AbsoluteFill>
      {/* beams */}
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {docs.map((d, i) => {
          const p = pos(i);
          const sx = portrait ? p.x + p.w / 2 : i < 3 ? p.x + p.w : p.x;
          const sy = portrait ? p.y : p.y + p.h / 2;
          const k = ease(frame, readAt + i * 3, readAt + i * 3 + 18);
          return (
            <line key={i} x1={sx} y1={sy} x2={sx + (cx - sx) * k} y2={sy + (cy - sy) * k} stroke={docColors[i]} strokeWidth={3} strokeDasharray="10 12" strokeDashoffset={frame * 2} opacity={0.85 * k} style={{ filter: `drop-shadow(0 0 6px ${docColors[i]})` }} />
          );
        })}
      </svg>
      {/* agent core */}
      <div style={{ position: "absolute", left: cx - orbSize / 2, top: cy - orbSize / 2, transform: `scale(${orbS * (reading ? 1 + 0.04 * Math.sin(frame / 4) : 1)})` }}>
        <Orb3D size={orbSize} color={reading ? C.green : C.cyan} color2={C.violet} pulse={reading ? 1 : 0} />
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: 96, height: 96, borderRadius: 26, background: `${C.bg}EE`, border: `2px solid ${reading ? C.green : C.cyan}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <ICpu size={54} color={C.text} />
          </div>
        </div>
      </div>
      {/* guessing question marks */}
      {isFinite(guessAt) &&
        Array.from({ length: 7 }).map((_, i) => {
          const a = (i / 7) * Math.PI * 2 + frame / 40;
          const r = 250 + Math.sin(frame / 15 + i) * 20;
          const k = ease(frame, guessAt + i * 4, guessAt + i * 4 + 12) * guessFade;
          return (
            <div key={i} style={{ position: "absolute", left: cx + Math.cos(a) * r - 30, top: cy + Math.sin(a) * r * 0.75 - 40, fontFamily: FONT, fontWeight: 900, fontSize: 70, color: C.red, opacity: k, textShadow: `0 0 20px ${C.red}` }}>
              ?
            </div>
          );
        })}
      {isFinite(guessAt) && (
        <div style={{ position: "absolute", left: 0, right: 0, top: portrait ? height * 0.42 : 140, textAlign: "center", opacity: ease(frame, first(word("guessing."), guessAt + 60), first(word("guessing."), guessAt + 60) + 10) * guessFade }}>
          <Pill color={C.red} size={34}>AI mistakes come from guessing</Pill>
        </div>
      )}
      {/* cards */}
      {docs.map((d, i) => {
        const p = pos(i);
        const s = useSpring(cues[i]);
        const live = frame >= cues[i] && (i === 5 || frame < cues[i + 1]) && frame < readAt;
        const col = docColors[i];
        return (
          <div key={d.k} style={{ position: "absolute", left: p.x, top: p.y, width: p.w, height: p.h, perspective: 1000 }}>
            <div
              style={{
                width: "100%",
                height: "100%",
                transform: `rotateY(${(1 - s) * (portrait ? 0 : i < 3 ? -90 : 90)}deg) rotateX(${portrait ? (1 - s) * 90 : 0}deg) scale(${live ? 1.05 : 1})`,
                opacity: Math.min(1, s * 1.5),
                borderRadius: 20,
                background: `linear-gradient(150deg, ${col}26, ${C.panel}F5 55%)`,
                border: `2px solid ${live || reading ? col : col + "55"}`,
                boxShadow: live ? `0 0 50px ${col}66` : "0 20px 50px #0008",
                padding: "22px 26px",
                display: "flex",
                gap: 20,
                alignItems: "center",
                boxSizing: "border-box",
              }}
            >
              <div style={{ width: 74, height: 74, flexShrink: 0, borderRadius: 18, background: `${col}22`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <d.I size={42} color={col} />
              </div>
              <div style={{ fontFamily: FONT, minWidth: 0 }}>
                <div style={{ fontSize: 36, fontWeight: 800, color: C.text }}>{d.t}</div>
                <div style={{ fontSize: 22, color: C.muted, fontWeight: 500, marginTop: 4 }}>{d.d}</div>
                <div style={{ fontFamily: MONO, fontSize: 17, color: col, marginTop: 6 }}>{d.f}</div>
              </div>
            </div>
          </div>
        );
      })}
      {/* outcome */}
      <div style={{ position: "absolute", left: 0, right: 0, top: portrait ? height * 0.36 : cy + orbSize / 2 - 10, display: "flex", justifyContent: "center", gap: 16, flexWrap: "wrap", opacity: ease(frame, readAt + 20, readAt + 34) }}>
        <Pill color={C.green} size={portrait ? 30 : 26}>✓ reads first · follows recorded decisions</Pill>
      </div>
      {isFinite(winAt) && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 70, display: "flex", justifyContent: "center", gap: 18, opacity: ease(frame, winAt, winAt + 14) }}>
          <Pill color={C.cyan} size={30}>fewer guesses → fewer errors</Pill>
          <Pill color={C.amber} size={30} style={{ opacity: ease(frame, first(word("documentation"), winAt + 40), first(word("documentation"), winAt + 40) + 12) }}>
            docs stay current
          </Pill>
        </div>
      )}
    </AbsoluteFill>
  );
};
