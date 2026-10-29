import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "../theme";
import { useScene, useSpring, ease, first } from "../timing";
import { VSWindow, Agent, Status } from "../components/VSWindow";
import { Glass } from "../components/ui";
import { IWarn } from "../components/Icons";

const agents: Agent[] = ["claude", "codex", "claude", "codex"];
const ctx = [
  { k: "decided.", t: "What was decided", c: C.violet },
  { k: "changed.", t: "What changed", c: C.cyan },
  { k: "tested.", t: "What was tested", c: C.green },
  { k: "left.", t: "What's left", c: C.amber },
];

export const Limit: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait, word, sentence, variant } = useScene();
  const meterAt = variant === "long" ? sentence(0) : 0;
  const wallAt = first(word("wall."), word("limit,"), word("limit"));
  const ctxBase = first(word("context."), word("context"));
  const cues = ctx.map((c, i) => first(word(c.k), ctxBase + 6 + i * 6));
  const crumbleAt = first(word("zero."), ctxBase + 50);
  const fill = ease(frame, meterAt + 5, first(wallAt, meterAt + 90), 0.35, 1);
  const meterS = useSpring(meterAt);
  const ww = portrait ? 470 : 400;
  const wh = ww * 0.62;
  const rowY = portrait ? height * 0.46 : height * 0.43;
  const crumble = ease(frame, crumbleAt, crumbleAt + 30);
  const winFade = 1 - ease(frame, ctxBase - 10, ctxBase + 10) * 0.6;

  return (
    <AbsoluteFill>
      {/* usage meter */}
      <div style={{ position: "absolute", left: portrait ? 60 : width / 2 - 520, top: portrait ? height * 0.16 : 150, width: portrait ? width - 120 : 1040, opacity: meterS, transform: `translateY(${(1 - meterS) * -30}px)` }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: FONT, fontSize: 28, fontWeight: 700, color: C.text, marginBottom: 12 }}>
          <span>Subscription usage</span>
          <span style={{ fontFamily: MONO, color: fill > 0.97 ? C.red : C.muted }}>{fill > 0.97 ? "limit reached" : "in use"}</span>
        </div>
        <div style={{ height: 30, borderRadius: 99, background: "#ffffff12", overflow: "hidden", border: "1.5px solid #ffffff18" }}>
          <div style={{ width: `${fill * 100}%`, height: "100%", borderRadius: 99, background: `linear-gradient(90deg, ${C.green}, ${C.amber} 60%, ${C.red})`, boxShadow: `0 0 20px ${fill > 0.97 ? C.red : C.amber}` }} />
        </div>
      </div>
      {/* windows */}
      <div style={{ position: "absolute", left: 0, right: 0, top: rowY - (portrait ? wh + 20 : wh / 2), display: "flex", flexWrap: "wrap", justifyContent: "center", gap: portrait ? 40 : 36, opacity: winFade, padding: portrait ? "0 40px" : 0 }}>
        {agents.map((a, i) => {
          let status: Status = "working";
          if (i === 2 && frame >= wallAt) status = "limit";
          const s = useSpring(meterAt + 8 + i * 4);
          return (
            <div key={i} style={{ opacity: s, transform: `translateY(${(1 - s) * 40}px) scale(${i === 2 && frame >= wallAt ? 1.06 : 1})` }}>
              <VSWindow agent={a} width={ww} height={wh} seed={i + 7} status={status} writeAt={0} focus={i === 2 && frame >= wallAt ? 1 : 0} />
            </div>
          );
        })}
      </div>
      {frame >= wallAt && (
        <div style={{ position: "absolute", left: 0, right: 0, top: portrait ? rowY + wh + 80 : rowY + wh / 2 + 40, display: "flex", justifyContent: "center", opacity: ease(frame, wallAt, wallAt + 8) * winFade }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14, fontFamily: FONT, fontWeight: 800, fontSize: 34, color: C.red }}>
            <IWarn size={40} color={C.red} /> mid-task. The work stops.
          </div>
        </div>
      )}
      {/* context chips */}
      {isFinite(ctxBase) && (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <Glass glow={crumble > 0.5 ? C.red : C.cyan} style={{ padding: portrait ? "36px 40px" : "36px 50px", opacity: ease(frame, ctxBase - 6, ctxBase + 8), transform: `translateY(${portrait ? -height * 0.08 : 20}px)`, width: portrait ? width - 140 : 980 }}>
            <div style={{ fontFamily: FONT, fontSize: 30, fontWeight: 700, color: C.muted, marginBottom: 24 }}>
              The real cost: <span style={{ color: crumble > 0.5 ? C.red : C.text }}>{crumble > 0.5 ? "context lost" : "context"}</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: portrait ? "1fr" : "1fr 1fr", gap: 20 }}>
              {ctx.map((c, i) => {
                const s = ease(frame, cues[i], cues[i] + 12);
                const fall = Math.max(0, crumble * 1.4 - i * 0.12);
                return (
                  <div key={i} style={{ padding: "20px 26px", borderRadius: 16, border: `2px solid ${c.c}88`, background: `${c.c}18`, fontFamily: FONT, fontWeight: 700, fontSize: 32, color: C.text, opacity: s * (1 - Math.min(1, fall)), transform: `translateY(${(1 - s) * 20 + fall * 120}px) rotate(${fall * (i % 2 ? 12 : -10)}deg)` }}>
                    {c.t}
                  </div>
                );
              })}
            </div>
            {crumble > 0.3 && (
              <div style={{ textAlign: "center", fontFamily: FONT, fontWeight: 900, fontSize: 64, color: C.red, opacity: crumble, marginTop: -40, textShadow: `0 0 30px ${C.red}` }}>next session starts from 0</div>
            )}
          </Glass>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
