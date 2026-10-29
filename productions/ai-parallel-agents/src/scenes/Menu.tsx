import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "../theme";
import { useScene, useSpring, ease, first } from "../timing";
import { Glass, Pill } from "../components/ui";
import { IKey, ILock, IUser, IX, ICpu } from "../components/Icons";

export const Menu: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait, word, sentence, variant } = useScene();
  const long = variant === "long";
  const subAt = word("subscription,");
  const orAt = first(word("openrouter."), word("openrouter,"), word("openrouter"));
  const capAt = word("cap");
  const neverAt = long ? sentence(2) : Infinity;
  const callAt = long ? word("call.") : word("choose.");
  const menuS = useSpring(2);
  const sel = frame >= orAt ? 1 : 0;
  const menuW = portrait ? width - 120 : 860;
  const menuLeft = portrait ? 60 : 110;
  const menuTop = portrait ? height * 0.17 : height * 0.5 - 230;
  const crossItems = [
    ["choose the provider", "chooses"],
    ["spend credit", "spend"],
    ["change credentials", "credentials,"],
    ["restart processes", "restart"],
  ];
  const right = portrait ? { left: 60, right: 60, top: height * 0.52 } : { left: 1030, right: 90, top: height * 0.5 - 260 };
  const showCross = isFinite(neverAt) && frame >= neverAt - 5;
  return (
    <AbsoluteFill>
      <Glass glow={C.cyan} style={{ position: "absolute", left: menuLeft, top: menuTop, width: menuW, padding: 0, overflow: "hidden", opacity: menuS, transform: `perspective(1400px) rotateY(${portrait ? 0 : (1 - menuS) * 25 + 6}deg)` }}>
        <div style={{ background: "#151B2B", padding: "14px 24px", fontFamily: MONO, fontSize: 22, color: C.muted, display: "flex", gap: 10, alignItems: "center" }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => (
            <div key={c} style={{ width: 13, height: 13, borderRadius: 99, background: c }} />
          ))}
          <span style={{ marginLeft: 14 }}>launcher</span>
        </div>
        <div style={{ padding: "30px 36px", fontFamily: MONO, color: C.text, fontSize: portrait ? 34 : 34, lineHeight: 1.5 }}>
          <div style={{ color: C.green }}>✔ checkpoint ready</div>
          <div style={{ color: C.muted, marginBottom: 18 }}>Choose a provider to continue:</div>
          {[
            ["Subscription", "default", C.claude, subAt],
            ["OpenRouter", "pay-as-you-go", C.violet, orAt],
          ].map(([t, d, c, at], i) => {
            const on = sel === i && frame >= (at as number) - 3;
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 18, padding: "14px 20px", borderRadius: 14, marginBottom: 10, background: on ? `${c}26` : "transparent", border: `2px solid ${on ? c : "transparent"}`, boxShadow: on ? `0 0 30px ${c}44` : "none" }}>
                <span style={{ color: on ? (c as string) : C.dim }}>{on ? "❯" : " "}</span>
                <span style={{ fontWeight: 700 }}>
                  {i + 1}) {t as string}
                </span>
                <span style={{ marginLeft: "auto", fontSize: 24, color: c as string }}>{d as string}</span>
              </div>
            );
          })}
        </div>
      </Glass>
      {/* OpenRouter key + cap */}
      <div style={{ position: "absolute", ...right, opacity: ease(frame, long ? sentence(1) : first(capAt - 40, orAt + 20), (long ? sentence(1) : first(capAt - 40, orAt + 20)) + 14) * (showCross ? 1 - ease(frame, neverAt - 5, neverAt + 10) : 1) }}>
        <Glass glow={C.violet} style={{ padding: 34 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 18, fontFamily: FONT, fontWeight: 800, fontSize: 36, color: C.text }}>
            <IKey size={46} color={C.violet} /> OpenRouter API key
          </div>
          <div style={{ fontFamily: FONT, fontSize: 26, color: C.muted, margin: "10px 0 30px" }}>pay only for what you use</div>
          <Cap at={capAt} />
        </Glass>
      </div>
      {/* agent never decides */}
      {showCross && (
        <div style={{ position: "absolute", ...right, opacity: ease(frame, neverAt, neverAt + 12) }}>
          <Glass glow={C.red} style={{ padding: 34 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, fontFamily: FONT, fontWeight: 800, fontSize: 34, color: C.text, marginBottom: 22 }}>
              <ICpu size={42} color={C.red} /> The agent never…
            </div>
            {crossItems.map(([t, w], i) => {
              const cue = first(word(w, 0, neverAt - 5), neverAt + 15 + i * 12);
              const k = ease(frame, cue, cue + 10);
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 16, fontFamily: FONT, fontSize: 32, fontWeight: 700, color: C.text, marginBottom: 14, opacity: 0.25 + k * 0.75 }}>
                  <IX size={34} color={C.red} stroke={3} />
                  <span style={{ position: "relative" }}>
                    {t}
                    <span style={{ position: "absolute", left: 0, top: "55%", height: 3, width: `${k * 100}%`, background: C.red }} />
                  </span>
                </div>
              );
            })}
          </Glass>
        </div>
      )}
      {isFinite(callAt) && (
        <div style={{ position: "absolute", left: 0, right: 0, top: portrait ? height * 0.43 : 120, display: "flex", justifyContent: "center", opacity: ease(frame, callAt - 4, callAt + 8) }}>
          <Pill color={C.amber} size={portrait ? 40 : 36}>
            <IUser size={40} color={C.amber} /> You make the call
          </Pill>
        </div>
      )}
    </AbsoluteFill>
  );
};

const Cap: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const used = ease(frame, at - 30, at + 30, 0, 0.42);
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: MONO, fontSize: 22, color: C.muted, marginBottom: 10 }}>
        <span>spend</span>
        <span style={{ color: C.amber, opacity: ease(frame, at, at + 10) }}>cap set by you</span>
      </div>
      <div style={{ position: "relative", height: 26, borderRadius: 99, background: "#ffffff12" }}>
        <div style={{ width: `${used * 100}%`, height: "100%", borderRadius: 99, background: `linear-gradient(90deg, ${C.cyan}, ${C.violet})` }} />
        <div style={{ position: "absolute", left: "82%", top: -12, width: 4, height: 50, background: C.amber, opacity: ease(frame, at, at + 10), boxShadow: `0 0 12px ${C.amber}` }} />
        <div style={{ position: "absolute", left: "82%", top: 44, transform: "translateX(-50%)", opacity: ease(frame, at, at + 10) }}>
          <ILock size={30} color={C.amber} />
        </div>
      </div>
      <div style={{ height: 30 }} />
    </div>
  );
};
