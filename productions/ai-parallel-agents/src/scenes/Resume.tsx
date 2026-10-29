import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "../theme";
import { useScene, useSpring, ease, first } from "../timing";
import { Glass, Pill, typed, Caret, Title, Grad } from "../components/ui";
import { AgentMark } from "../components/VSWindow";
import { IDoc, ICheck, IX, ITarget, IEye, IPlay } from "../components/Icons";

export const Resume: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait, word, sentence, variant, length } = useScene();
  const long = variant === "long";
  const p1 = long ? sentence(1) : Infinity;
  const p2 = long ? sentence(2) : Infinity;
  const p3 = long ? sentence(3) : sentence(1);
  const phase = frame >= p3 ? 3 : frame >= p2 ? 2 : frame >= p1 ? 1 : 0;
  const fadeIn = (at: number) => ease(frame, at, at + 14);
  const termW = portrait ? width - 120 : 1100;
  return (
    <AbsoluteFill>
      {phase === 0 && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <Glass glow={C.green} style={{ width: termW, padding: "30px 40px", fontFamily: MONO, fontSize: portrait ? 30 : 34, color: C.text, lineHeight: 1.7, transform: `translateY(${portrait ? -120 : -30}px)`, opacity: fadeIn(0) }}>
            <div style={{ color: C.muted }}>{typed("● new session started", frame, 4, 40)}</div>
            <div>
              {typed("› read ", frame, 22, 40)}
              <span style={{ color: C.amber }}>{typed("memory/checkpoint.md", frame, 30, 40)}</span>
            </div>
            <div style={{ color: C.green }}>{typed("✓ goal · decisions · state loaded", frame, first(word("reads"), 60) + 10, 40)}</div>
            <div style={{ color: C.cyan }}>
              {typed("› continue with the next action", frame, first(word("anything"), word("continues."), 100), 40)}
              <Caret frame={frame} color={C.cyan} />
            </div>
          </Glass>
          <div style={{ position: "absolute", left: width / 2 - 60 + (1 - ease(frame, 8, 34)) * -500, top: (portrait ? height * 0.27 : height * 0.12) + (1 - ease(frame, 8, 34)) * -80, opacity: 1 - ease(frame, 34, 42) }}>
            <IDoc size={120} color={C.amber} stroke={1.5} />
          </div>
        </AbsoluteFill>
      )}
      {phase === 1 && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: portrait ? "column" : "row", gap: 60 }}>
          <Glass style={{ width: portrait ? width - 160 : 640, padding: 40, opacity: fadeIn(p1) * 0.85 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14, fontFamily: FONT, fontSize: 36, fontWeight: 800, color: C.red, marginBottom: 24 }}>
              <IX size={40} color={C.red} stroke={3} /> Replay old chat
            </div>
            {[0.8, 0.55, 0.7, 0.4].map((w, i) => (
              <div key={i} style={{ height: 34, width: `${w * 100}%`, marginLeft: i % 2 ? "auto" : 0, borderRadius: 14, background: "#ffffff12", marginBottom: 14 }} />
            ))}
          </Glass>
          <Glass glow={C.green} style={{ width: portrait ? width - 160 : 640, padding: 40, opacity: fadeIn(first(word("clean,"), p1 + 40)), transform: `scale(${0.95 + 0.05 * fadeIn(first(word("clean,"), p1 + 40))})` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14, fontFamily: FONT, fontSize: 36, fontWeight: 800, color: C.green, marginBottom: 24 }}>
              <ICheck size={40} color={C.green} stroke={3} /> Written handoff
            </div>
            {["goal", "decisions", "changes", "verified checks", "next action"].map((t) => (
              <div key={t} style={{ display: "flex", alignItems: "center", gap: 12, fontFamily: MONO, fontSize: 26, color: C.text, marginBottom: 8 }}>
                <IDoc size={24} color={C.amber} /> {t}
              </div>
            ))}
          </Glass>
        </AbsoluteFill>
      )}
      {phase === 2 && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ display: "grid", gridTemplateColumns: portrait ? "1fr 1fr" : "repeat(4, 1fr)", gap: 30, transform: `translateY(${portrait ? -150 : -20}px)` }}>
            {[
              ["Goal", "goal,", ITarget, C.violet],
              ["Done", "done,", ICheck, C.cyan],
              ["Verified", "verified,", IEye, C.green],
              ["Next", "next.", IPlay, C.amber],
            ].map(([t, w, I, c], i) => {
              const at = first(word(w as string, 0, p2), p2 + i * 15);
              const s = ease(frame, at - 2, at + 12);
              const Icon = I as React.FC<{ size: number; color: string }>;
              return (
                <div key={i} style={{ width: portrait ? 400 : 330, height: 260, borderRadius: 26, border: `2px solid ${c}`, background: `linear-gradient(160deg, ${c}30, ${C.panel}F5 60%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 20, opacity: 0.15 + s * 0.85, transform: `translateY(${(1 - s) * 40}px) scale(${0.9 + s * 0.1})`, boxShadow: `0 0 ${s * 50}px ${c}55` }}>
                  <Icon size={80} color={c as string} />
                  <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 44, color: C.text }}>{t as string}</div>
                </div>
              );
            })}
          </div>
        </AbsoluteFill>
      )}
      {phase === 3 && long && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 40 }}>
          <div style={{ width: portrait ? width - 140 : 1100 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: FONT, fontWeight: 800, fontSize: 40, color: C.text, marginBottom: 18 }}>
              <span>Task</span>
              <span style={{ fontFamily: MONO, color: C.green }}>{Math.round(ease(frame, p3, p3 + 60) * 100)}%</span>
            </div>
            <div style={{ height: 36, borderRadius: 99, background: "#ffffff12", overflow: "hidden" }}>
              <div style={{ width: `${ease(frame, p3, p3 + 60) * 100}%`, height: "100%", borderRadius: 99, background: `linear-gradient(90deg, ${C.cyan}, ${C.green})`, boxShadow: `0 0 30px ${C.green}` }} />
            </div>
          </div>
          <div style={{ display: "flex", gap: 20, flexWrap: "wrap", justifyContent: "center", maxWidth: width - 120 }}>
            {["task finished", "docs updated", "fewer mistakes"].map((t, i) => (
              <Pill key={t} color={C.green} size={32} style={{ opacity: ease(frame, p3 + 30 + i * 12, p3 + 42 + i * 12) }}>
                ✓ {t}
              </Pill>
            ))}
          </div>
        </AbsoluteFill>
      )}
      {phase === 3 && !long && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 40, transform: "translateY(-160px)" }}>
          <div style={{ display: "flex", gap: 24, opacity: fadeIn(p3) }}>
            <Pill color={C.claude} size={32}>
              <AgentMark agent="claude" size={32} />
            </Pill>
            <Pill color={C.codex} size={32}>
              <AgentMark agent="codex" size={32} />
            </Pill>
          </div>
          <Title size={96} style={{ textAlign: "center", opacity: fadeIn(first(word("ship"), p3 + 40)) }}>
            Ship faster
            <br />
            <Grad>in the AI era</Grad>
          </Title>
        </AbsoluteFill>
      )}
      <div style={{ display: "none" }}>{length}</div>
    </AbsoluteFill>
  );
};
