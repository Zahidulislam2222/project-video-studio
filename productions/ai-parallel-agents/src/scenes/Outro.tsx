import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "../theme";
import { useScene, useSpring, ease, first } from "../timing";
import { Orb3D } from "../components/Orb3D";
import { IGlobe, IMail } from "../components/Icons";

export const PORTFOLIO_URL = "zahidul-islam.com";

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait, word } = useScene();
  const q = useSpring(4);
  const urlAt = first(word("portfolio."), 60);
  const u = useSpring(urlAt - 6);
  const orb = portrait ? 380 : 320;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 34, transform: portrait ? "translateY(-160px)" : "translateY(-50px)" }}>
        <div style={{ marginBottom: -40, transform: `scale(${q})` }}>
          <Orb3D size={orb} spin={0.6} />
        </div>
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: portrait ? 80 : 92, color: C.text, opacity: q, transform: `translateY(${(1 - q) * 30}px)`, textAlign: "center", letterSpacing: -2 }}>Have a question?</div>
        <div style={{ display: "flex", alignItems: "center", gap: 16, fontFamily: FONT, fontWeight: 600, fontSize: portrait ? 40 : 40, color: C.muted, opacity: ease(frame, 18, 32) }}>
          <IMail size={44} color={C.cyan} /> Contact me
        </div>
        <div style={{ marginTop: 10, padding: portrait ? "26px 44px" : "26px 56px", borderRadius: 26, border: `2.5px solid ${C.cyan}`, background: `${C.bg}DD`, boxShadow: `0 0 ${40 + 20 * Math.sin(frame / 10)}px ${C.cyan}77`, display: "flex", alignItems: "center", gap: 22, transform: `scale(${0.7 + u * 0.3})`, opacity: u }}>
          <IGlobe size={portrait ? 54 : 60} color={C.cyan} />
          <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: portrait ? 56 : 66, color: C.text }}>{PORTFOLIO_URL}</span>
        </div>
        <div style={{ fontFamily: FONT, fontSize: 28, color: C.dim, opacity: ease(frame, urlAt + 20, urlAt + 35), letterSpacing: 4, textTransform: "uppercase" }}>portfolio</div>
      </div>
    </AbsoluteFill>
  );
};
