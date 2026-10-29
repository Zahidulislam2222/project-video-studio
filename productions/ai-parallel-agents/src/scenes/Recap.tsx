import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT } from "../theme";
import { useScene, useSpring, ease } from "../timing";
import { Title, Grad } from "../components/ui";
import { ILayers, IDoc, ISwitch } from "../components/Icons";

const pillars = [
  { t: "Run in parallel", d: "stay the reviewer", I: ILayers, c: C.cyan },
  { t: "Written context", d: "agents never guess", I: IDoc, c: C.violet },
  { t: "Checkpoint → switch", d: "and continue", I: ISwitch, c: C.green },
];

export const Recap: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const { portrait, sentence } = useScene();
  const finalAt = sentence(4);
  const outro = ease(frame, finalAt - 6, finalAt + 14);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", perspective: 1600, opacity: 1 - outro, transform: `scale(${1 - outro * 0.1})` }}>
        <div style={{ display: "flex", flexDirection: portrait ? "column" : "row", gap: 40, transform: portrait ? "translateY(-120px)" : "translateY(-30px)" }}>
          {pillars.map((p, i) => {
            const s = useSpring(sentence(i + 1));
            return (
              <div key={i} style={{ width: portrait ? width - 200 : 500, height: portrait ? 270 : 420, borderRadius: 30, background: `linear-gradient(170deg, ${p.c}33, ${C.panel}F5 55%)`, border: `2px solid ${p.c}`, boxShadow: `0 30px 80px #000A, 0 0 50px ${p.c}33`, display: "flex", flexDirection: portrait ? "row" : "column", alignItems: "center", justifyContent: "center", gap: 26, padding: 30, transform: `rotateX(${(1 - s) * 70}deg) translateY(${(1 - s) * 120}px)`, opacity: s, transformOrigin: "50% 100%", boxSizing: "border-box" }}>
                <div style={{ width: 120, height: 120, borderRadius: 32, background: `${p.c}22`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <p.I size={70} color={p.c} />
                </div>
                <div style={{ textAlign: portrait ? "left" : "center", fontFamily: FONT }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: p.c, letterSpacing: 3 }}>0{i + 1}</div>
                  <div style={{ fontSize: 46, fontWeight: 800, color: C.text, lineHeight: 1.1 }}>{p.t}</div>
                  <div style={{ fontSize: 28, color: C.muted, marginTop: 8 }}>{p.d}</div>
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
      {isFinite(finalAt) && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 30, opacity: outro, transform: portrait ? "translateY(-150px)" : "translateY(-40px)" }}>
          <Title size={portrait ? 74 : 92} style={{ textAlign: "center", color: C.muted, position: "relative" }}>
            Speed ≠ typing faster
            <div style={{ position: "absolute", left: 0, top: "52%", height: 6, width: `${ease(frame, finalAt + 30, finalAt + 50) * 100}%`, background: C.red }} />
          </Title>
          <Title size={portrait ? 74 : 100} style={{ textAlign: "center", opacity: ease(frame, finalAt + 60, finalAt + 80) }}>
            Speed = <Grad a={C.amber} b={C.claude}>using the tools properly</Grad>
          </Title>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
