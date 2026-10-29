import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C } from "../theme";

/** Dark stage with a perspective grid floor that keeps moving forward, drifting glows and a vignette. */
export const Background: React.FC<{ accent?: string; accent2?: string }> = ({ accent = C.cyan, accent2 = C.violet }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const t = frame / 30;
  const move = (frame * 2.2) % 80;
  const big = Math.max(width, height);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(120% 90% at 50% 0%, ${C.bg2} 0%, ${C.bg} 60%)`, overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          width: big * 0.9,
          height: big * 0.9,
          left: width * 0.5 - big * 0.45 + Math.sin(t * 0.3) * width * 0.18,
          top: height * 0.15 - big * 0.45 + Math.cos(t * 0.25) * height * 0.08,
          background: `radial-gradient(circle, ${accent}2E 0%, transparent 60%)`,
          filter: "blur(30px)",
        }}
      />
      <div
        style={{
          position: "absolute",
          width: big * 0.8,
          height: big * 0.8,
          left: width * 0.5 - big * 0.4 + Math.cos(t * 0.21) * width * 0.25,
          top: height * 0.6 - big * 0.4 + Math.sin(t * 0.33) * height * 0.1,
          background: `radial-gradient(circle, ${accent2}26 0%, transparent 62%)`,
          filter: "blur(30px)",
        }}
      />
      {/* Perspective grid floor */}
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: height * 0.55, perspective: 700, perspectiveOrigin: "50% 0%", overflow: "hidden", maskImage: "linear-gradient(to bottom, transparent, black 45%)", WebkitMaskImage: "linear-gradient(to bottom, transparent, black 45%)" }}>
        <div
          style={{
            position: "absolute",
            left: "-100%",
            width: "300%",
            top: 0,
            height: "300%",
            transform: "rotateX(72deg)",
            transformOrigin: "50% 0%",
            backgroundImage: `linear-gradient(${accent}30 1.5px, transparent 1.5px), linear-gradient(90deg, ${accent}30 1.5px, transparent 1.5px)`,
            backgroundSize: "80px 80px",
            backgroundPosition: `0px ${move}px`,
          }}
        />
      </div>
      {/* Dust particles */}
      {Array.from({ length: 36 }).map((_, i) => {
        const seed = (i * 9301 + 49297) % 233280;
        const r = seed / 233280;
        const x = ((r * 1.7 + i * 0.137) % 1) * width;
        const speed = 0.15 + ((i * 37) % 10) / 30;
        const y = height - (((frame * speed * 2 + i * 97) % (height + 40)));
        const s = 1.5 + (i % 3);
        return <div key={i} style={{ position: "absolute", left: x, top: y, width: s, height: s, borderRadius: 9, background: i % 2 ? accent : C.text, opacity: 0.18 + (i % 4) * 0.06 }} />;
      })}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, transparent 55%, #000000B0 100%)" }} />
    </AbsoluteFill>
  );
};
