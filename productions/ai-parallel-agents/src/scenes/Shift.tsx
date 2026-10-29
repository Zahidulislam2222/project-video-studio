import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "../theme";
import { useScene, useSpring, ease, first } from "../timing";
import { Glass, Pill } from "../components/ui";
import { IUser, ICpu, ICheck } from "../components/Icons";

const colors = [C.claude, C.codex, C.violet, C.cyan];

export const Shift: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait, word, sentence } = useScene();
  const splitAt = first(word("change"), sentence(1));
  const rolesAt = sentence(2);
  const upAt = first(word("level."), word("level"));
  const parAt = sentence(3);
  const split = ease(frame, splitAt + 6, splitAt + 40);
  const side = ease(frame, rolesAt - 4, rolesAt + 26);

  // Lane area geometry
  const areaW = portrait ? width * 0.86 : width * (0.62 - side * 0.17);
  const areaX = portrait ? (width - areaW) / 2 : (width - areaW) / 2 - side * width * 0.22;
  const areaY = portrait ? height * 0.2 - side * 0 : height * 0.5 - 170;
  const bw = areaW / 4.3;
  const laneGap = 76;
  const seqY = areaY + 150;
  const playhead = ((frame % 150) / 150) * areaW;
  const seqProgress = Math.min(4, frame / 28);

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: areaX, top: areaY - 10, width: areaW, fontFamily: FONT }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ position: "relative", height: 50, width: 600 }}>
            <div style={{ position: "absolute", fontSize: 34, fontWeight: 800, color: C.muted, opacity: 1 - split }}>Before: one line</div>
            <div style={{ position: "absolute", fontSize: 34, fontWeight: 800, color: C.text, opacity: split }}>
              With agents: <span style={{ color: C.cyan }}>parallel lanes</span>
            </div>
          </div>
        </div>
      </div>
      {/* lanes */}
      {[0, 1, 2, 3].map((i) => {
        const y = seqY + split * (i - 1.5) * laneGap + split * 60;
        const x = areaX + (1 - split) * i * (bw * 1.08);
        const fillSeq = Math.max(0, Math.min(1, seqProgress - i));
        const fillPar = ease(frame, splitAt + 40 + i * 4, (isFinite(parAt) ? parAt : splitAt + 200) + 60 + i * 10, 0.08, 1);
        const fill = split < 0.5 ? fillSeq : Math.max(fillPar, 0.08);
        const w = bw * (1 - split) + split * areaW * 0.92;
        return (
          <React.Fragment key={i}>
            <div style={{ position: "absolute", left: areaX, top: y - 2 + 26, width: areaW, height: 4, background: "#ffffff10", opacity: split }} />
            <div style={{ position: "absolute", left: x, top: y, width: w, height: 56, borderRadius: 14, background: "#ffffff08", border: `1.5px solid ${colors[i]}55`, overflow: "hidden" }}>
              <div style={{ width: `${fill * 100}%`, height: "100%", background: `linear-gradient(90deg, ${colors[i]}55, ${colors[i]}AA)` }} />
              <div style={{ position: "absolute", left: 16, top: 0, height: "100%", display: "flex", alignItems: "center", gap: 10, fontFamily: MONO, fontSize: 22, fontWeight: 700, color: C.text }}>
                project {i + 1}
                {fill >= 0.999 && <ICheck size={22} color={C.text} />}
              </div>
            </div>
          </React.Fragment>
        );
      })}
      {/* sequential playhead */}
      <div style={{ position: "absolute", left: areaX + playhead, top: seqY - 20, width: 3, height: 96, background: C.amber, boxShadow: `0 0 16px ${C.amber}`, opacity: 1 - split }} />
      <div style={{ position: "absolute", left: areaX, top: seqY + 90, fontFamily: FONT, fontSize: 24, color: C.muted, opacity: 1 - split }}>pick one task → finish → start the next</div>
      {/* roles */}
      <Roles portrait={portrait} at={rolesAt} upAt={upAt} parAt={parAt} width={width} height={height} />
    </AbsoluteFill>
  );
};

const Roles: React.FC<{ portrait: boolean; at: number; upAt: number; parAt: number; width: number; height: number }> = ({ portrait, at, upAt, parAt, width, height }) => {
  const frame = useCurrentFrame();
  const a = useSpring(at);
  const b = useSpring(first(upAt, at + 30));
  const c = useSpring(parAt);
  const cardW = portrait ? width * 0.86 : 640;
  const left = portrait ? (width - cardW) / 2 : width * 0.6;
  const top = portrait ? height * 0.52 : height * 0.5 - 250;
  const chip = (t: string, col: string, d: number, base: number) => {
    const s = ease(frame, base + d, base + d + 12);
    return (
      <Pill key={t} color={col} size={26} style={{ opacity: s, transform: `translateY(${(1 - s) * 14}px)` }}>
        {t}
      </Pill>
    );
  };
  return (
    <div style={{ position: "absolute", left, top, width: cardW, display: "flex", flexDirection: "column", gap: 26, opacity: a, transform: `translateX(${(1 - a) * 80}px)` }}>
      <Glass glow={C.violet} style={{ padding: 30, transform: `translateY(${-b * 10}px)` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 18 }}>
          <div style={{ width: 58, height: 58, borderRadius: 16, background: `${C.violet}22`, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <IUser size={34} color={C.violet} />
          </div>
          <div style={{ fontFamily: FONT, fontSize: 34, fontWeight: 800, color: C.text }}>You</div>
          <div style={{ marginLeft: "auto", fontFamily: MONO, fontSize: 20, color: C.violet, opacity: b }}>▲ level up</div>
        </div>
        <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>{["Plan", "Review", "Decide"].map((t, i) => chip(t, C.violet, i * 7, first(upAt, at + 30)))}</div>
      </Glass>
      <div style={{ alignSelf: "center", width: 3, height: 34 * a, background: `linear-gradient(${C.violet}, ${C.cyan})` }} />
      <Glass glow={C.cyan} style={{ padding: 30 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 18 }}>
          <div style={{ width: 58, height: 58, borderRadius: 16, background: `${C.cyan}22`, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <ICpu size={34} color={C.cyan} />
          </div>
          <div style={{ fontFamily: FONT, fontSize: 34, fontWeight: 800, color: C.text }}>AI agent</div>
        </div>
        <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>{["Write", "Run", "Test"].map((t, i) => chip(t, C.cyan, i * 7, at + 8))}</div>
      </Glass>
      <div style={{ opacity: c, transform: `scale(${0.9 + c * 0.1})`, alignSelf: "center" }}>
        <Pill color={C.amber} size={26}>Reviewer, not typist → many projects at once</Pill>
      </div>
    </div>
  );
};
