import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MONO } from "../theme";
import { useScene, useSpring, ease, first } from "../timing";
import { Glass, Pill, typed, Caret } from "../components/ui";
import { AgentMark } from "../components/VSWindow";
import { ICheck, IX, IFolder, IDoc, IShield, IBranch, ILock, ITerminal } from "../components/Icons";

const STEPS = [
  { t: "Safe checkpoint", c: C.cyan },
  { t: "Structured handoff", c: C.violet },
  { t: "Save to private memory", c: C.amber },
  { t: "Secret scan", c: C.pink },
  { t: "Type /exit", c: C.green },
];

export const Skill: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait, word, sentence, variant } = useScene();
  const long = variant === "long";
  const invokeAt = long ? sentence(1) : first(word("switch-provider"), 8);
  const steps = long ? [sentence(2), sentence(3), sentence(5), sentence(6), sentence(7)] : [word("checkpoint,"), word("handoff."), word("memory,"), word("secrets,"), word("exit.")];
  const stepsAt = steps[0];
  const intro = 1 - ease(frame, stepsAt - 10, stepsAt + 12);
  let cur = -1;
  steps.forEach((s, i) => {
    if (frame >= s - 3) cur = i;
  });

  return (
    <AbsoluteFill>
      {intro > 0.01 && <Intro invokeAt={invokeAt} fade={intro} long={long} />}
      {frame >= stepsAt - 10 && (
        <AbsoluteFill style={{ opacity: 1 - intro }}>
          <Stepper cur={cur} steps={steps} portrait={portrait} />
          <div style={{ position: "absolute", transform: portrait ? "scale(1.22)" : undefined, ...(portrait ? { left: 150, right: 150, top: height * 0.3, height: height * 0.42 } : { left: 640, right: 90, top: 170, bottom: 190 }) }}>
            {cur === 0 && <StepCheckpoint at={steps[0]} />}
            {cur === 1 && <StepHandoff at={steps[1]} />}
            {cur === 2 && <StepSave at={steps[2]} />}
            {cur === 3 && <StepScan at={steps[3]} />}
            {cur === 4 && <StepExit at={steps[4]} />}
          </div>
        </AbsoluteFill>
      )}
      <div style={{ display: "none" }}>{width}</div>
    </AbsoluteFill>
  );
};

const Intro: React.FC<{ invokeAt: number; fade: number; long: boolean }> = ({ invokeAt, fade, long }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { portrait } = useScene();
  const t = useSpring(2);
  const inv = useSpring(invokeAt);
  const lift = ease(frame, invokeAt - 5, invokeAt + 20);
  const termW = portrait ? width - 140 : 720;
  return (
    <AbsoluteFill style={{ opacity: fade, transform: `scale(${0.94 + fade * 0.06})` }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: (portrait ? height * 0.36 : height * 0.36) - lift * (portrait ? 220 : 190), textAlign: "center", transform: `scale(${0.8 + t * 0.2})`, opacity: t }}>
        <div style={{ fontFamily: FONT, fontSize: 30, color: C.muted, fontWeight: 600, marginBottom: 12, letterSpacing: 4, textTransform: "uppercase" }}>a skill I built</div>
        <div style={{ fontFamily: MONO, fontSize: portrait ? 92 : 120, fontWeight: 700, color: C.text, textShadow: `0 0 40px ${C.cyan}AA` }}>
          <span style={{ color: C.cyan }}>switch</span>-provider
        </div>
        <div style={{ display: "flex", justifyContent: "center", gap: 26, marginTop: 30, opacity: ease(frame, 12, 30) }}>
          <Pill color={C.claude} size={28}>
            <AgentMark agent="claude" size={28} />
          </Pill>
          <Pill color={C.codex} size={28}>
            <AgentMark agent="codex" size={28} />
          </Pill>
        </div>
        {long && <div style={{ fontFamily: FONT, fontSize: 28, color: C.muted, marginTop: 20, opacity: ease(frame, 30, 45) * (1 - lift) }}>same behaviour in both</div>}
      </div>
      {isFinite(invokeAt) && (
        <div style={{ position: "absolute", left: 0, right: 0, top: portrait ? height * 0.5 : height * 0.56, display: "flex", flexDirection: portrait ? "column" : "row", alignItems: "center", justifyContent: "center", gap: 36, opacity: inv, transform: `translateY(${(1 - inv) * 50}px)` }}>
          {(["claude", "codex"] as const).map((a, i) => (
            <Glass key={a} glow={a === "claude" ? C.claude : C.codex} style={{ width: termW, padding: "22px 28px", fontFamily: MONO }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                <ITerminal size={26} color={C.muted} />
                <AgentMark agent={a} size={24} />
              </div>
              <div style={{ fontSize: 44, color: C.text }}>
                <span style={{ color: C.dim }}>{"> "}</span>
                {typed(a === "claude" ? "/switch-provider" : "$switch-provider", frame, invokeAt + 4 + i * 16, 22)}
                <Caret frame={frame} />
              </div>
            </Glass>
          ))}
        </div>
      )}
    </AbsoluteFill>
  );
};

const Stepper: React.FC<{ cur: number; steps: number[]; portrait: boolean }> = ({ cur, steps, portrait }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  if (portrait) {
    const y = height * 0.14;
    const gap = (width - 160) / 4;
    return (
      <div style={{ position: "absolute", left: 0, right: 0, top: y }}>
        <div style={{ position: "absolute", left: 80, width: width - 160, top: 34, height: 4, background: "#ffffff15" }} />
        <div style={{ position: "absolute", left: 80, width: Math.max(0, cur) * gap, top: 34, height: 4, background: `linear-gradient(90deg, ${C.cyan}, ${C.violet})` }} />
        {STEPS.map((s, i) => {
          const on = i === cur;
          const done = i < cur;
          return (
            <div key={i} style={{ position: "absolute", left: 80 + i * gap - 36, top: 0, width: 72, height: 72, borderRadius: 99, background: on ? s.c : done ? `${s.c}55` : C.panel, border: `3px solid ${on || done ? s.c : "#ffffff22"}`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: MONO, fontWeight: 700, fontSize: 30, color: on ? C.bg : C.text, transform: `scale(${on ? 1.15 : 1})`, boxShadow: on ? `0 0 30px ${s.c}` : "none" }}>
              {done ? <ICheck size={34} color={C.text} stroke={3} /> : i + 1}
            </div>
          );
        })}
        {cur >= 0 && (
          <div style={{ position: "absolute", left: 0, right: 0, top: 100, textAlign: "center", fontFamily: FONT, fontWeight: 800, fontSize: 46, color: STEPS[cur].c, opacity: ease(frame, steps[cur] - 3, steps[cur] + 8) }}>
            Step {cur + 1} · {STEPS[cur].t}
          </div>
        )}
      </div>
    );
  }
  return (
    <div style={{ position: "absolute", left: 100, top: 190, width: 500 }}>
      <div style={{ position: "absolute", left: 35, top: 40, width: 4, height: 4 * 132, background: "#ffffff15" }} />
      <div style={{ position: "absolute", left: 35, top: 40, width: 4, height: Math.max(0, cur) * 132, background: `linear-gradient(${C.cyan}, ${C.violet})` }} />
      {STEPS.map((s, i) => {
        const on = i === cur;
        const done = i < cur;
        const k = ease(frame, steps[0] - 10 + i * 4, steps[0] + 6 + i * 4);
        return (
          <div key={i} style={{ position: "absolute", top: i * 132, left: 0, display: "flex", alignItems: "center", gap: 24, opacity: k * (on ? 1 : done ? 0.85 : 0.45), transform: `translateX(${(1 - k) * -40 + (on ? 10 : 0)}px)` }}>
            <div style={{ width: 74, height: 74, borderRadius: 99, flexShrink: 0, background: on ? s.c : done ? `${s.c}44` : C.panel, border: `3px solid ${on || done ? s.c : "#ffffff22"}`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: MONO, fontWeight: 700, fontSize: 30, color: on ? C.bg : C.text, boxShadow: on ? `0 0 34px ${s.c}` : "none" }}>
              {done ? <ICheck size={34} color={C.text} stroke={3} /> : i + 1}
            </div>
            <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: on ? 36 : 30, color: on ? C.text : C.muted }}>{s.t}</div>
          </div>
        );
      })}
    </div>
  );
};

const Row: React.FC<{ ok: boolean; text: string; at: number; size?: number }> = ({ ok, text, at, size = 34 }) => {
  const frame = useCurrentFrame();
  const k = ease(frame, at, at + 12);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 18, opacity: k, transform: `translateX(${(1 - k) * 30}px)`, fontFamily: FONT, fontWeight: 700, fontSize: size, color: C.text }}>
      <div style={{ width: size * 1.4, height: size * 1.4, borderRadius: 12, flexShrink: 0, background: ok ? `${C.green}22` : `${C.red}22`, border: `2px solid ${ok ? C.green : C.red}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        {ok ? <ICheck size={size} color={C.green} stroke={3} /> : <IX size={size} color={C.red} stroke={3} />}
      </div>
      {text}
    </div>
  );
};

const StepCheckpoint: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const { word } = useScene();
  const p = ease(frame, at, at + 60);
  const r = 120;
  const c = 2 * Math.PI * r;
  return (
    <AbsoluteFill style={{ flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 40 }}>
      <div style={{ position: "relative", width: 300, height: 300 }}>
        <svg width={300} height={300}>
          <circle cx={150} cy={150} r={r} stroke="#ffffff15" strokeWidth={16} fill="none" />
          <circle cx={150} cy={150} r={r} stroke={C.cyan} strokeWidth={16} fill="none" strokeDasharray={c} strokeDashoffset={c * (1 - p)} strokeLinecap="round" transform="rotate(-90 150 150)" style={{ filter: `drop-shadow(0 0 10px ${C.cyan})` }} />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", fontFamily: FONT }}>
          {p > 0.99 ? <ICheck size={90} color={C.cyan} stroke={3} /> : <div style={{ fontSize: 64, fontWeight: 800, color: C.text, fontFamily: MONO }}>{Math.round(p * 100)}%</div>}
          <div style={{ fontSize: 22, color: C.muted, fontWeight: 600 }}>current step</div>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <Row ok text="Smallest safe checkpoint" at={at + 30} />
        <Row ok={false} text="No half-written changes" at={first(word("half-written"), at + 50)} />
        <Row ok={false} text="No commit just to switch" at={first(word("commits"), at + 70)} />
      </div>
    </AbsoluteFill>
  );
};

const StepHandoff: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const { word, sentence, variant, portrait } = useScene();
  const long = variant === "long";
  const fields = long
    ? [
        ["Goal", "goal,"],
        ["Constraints", "constraints,"],
        ["Decisions", "decisions,"],
        ["Changed files", "files,"],
        ["Tests actually run + results", "tests"],
        ["Failures", "failures,"],
        ["Remaining work", "remaining"],
        ["Blockers", "blockers,"],
        ["Next action", "next"],
      ]
    : [
        ["Goal", "goal,"],
        ["Decisions", "decisions,"],
        ["Changed files", "files,"],
        ["Real test results", "test"],
        ["Next steps", "next"],
      ];
  const neverAt = long ? sentence(4) : Infinity;
  const card = useSpring(at);
  const stamp = useSpring(neverAt);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <Glass glow={C.violet} style={{ width: portrait ? "100%" : 820, padding: "30px 40px", transform: `translateY(${(1 - card) * 40}px) rotateX(${(1 - card) * 20}deg)`, opacity: card, position: "relative" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, fontFamily: MONO, fontSize: 28, color: C.violet, marginBottom: 20 }}>
          <IDoc size={34} color={C.violet} /> checkpoint · handoff
        </div>
        <div style={{ display: "grid", gridTemplateColumns: long && !portrait ? "1fr 1fr" : "1fr", columnGap: 30, rowGap: long ? 16 : 22 }}>
          {fields.map(([label, w], i) => {
            const cue = first(word(w, 0, at - 5), at + 10 + i * 10);
            const k = ease(frame, cue - 2, cue + 10);
            const isTest = label.toLowerCase().includes("test");
            return (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 14, opacity: 0.2 + 0.8 * k, fontFamily: FONT, fontSize: long ? 29 : 36, fontWeight: 700, color: C.text, gridColumn: isTest && long && !portrait ? "1 / span 2" : undefined }}>
                <div style={{ width: 30, height: 30, borderRadius: 8, border: `2px solid ${k > 0.5 ? C.green : "#ffffff33"}`, background: k > 0.5 ? `${C.green}22` : "transparent", display: "flex", alignItems: "center", justifyContent: "center" }}>{k > 0.5 && <ICheck size={22} color={C.green} stroke={3} />}</div>
                <span style={{ color: isTest ? C.amber : C.text }}>{label}</span>
              </div>
            );
          })}
        </div>
        {isFinite(neverAt) && frame >= neverAt && (
          <div style={{ position: "absolute", right: 30, bottom: -36, transform: `rotate(-6deg) scale(${2 - stamp})`, opacity: stamp, padding: "14px 26px", border: `4px solid ${C.red}`, borderRadius: 14, color: C.red, background: `${C.bg}EE`, fontFamily: MONO, fontWeight: 700, fontSize: 32, boxShadow: `0 0 30px ${C.red}66` }}>
            not run ≠ passed
          </div>
        )}
      </Glass>
    </AbsoluteFill>
  );
};

const StepSave: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const { word, portrait } = useScene();
  const fly = ease(frame, at + 8, at + 40);
  const folder = useSpring(at);
  const gi = first(word("verifies"), at + 45);
  const git = first(word("git", 1, at), word("captures"), at + 70);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 34 }}>
      <div style={{ position: "relative", width: 640, height: 300 }}>
        <div style={{ position: "absolute", left: 320 - 130, top: 40, width: 260, height: 230, transform: `scale(${folder})`, display: "flex", flexDirection: "column", alignItems: "center" }}>
          <IFolder size={200} color={C.amber} stroke={1.4} />
          <div style={{ fontFamily: MONO, fontSize: 34, fontWeight: 700, color: C.text, marginTop: -10 }}>memory/</div>
        </div>
        <div style={{ position: "absolute", left: 40 + fly * 230, top: -20 + fly * 110, transform: `scale(${1 - fly * 0.5}) rotate(${(1 - fly) * -15}deg)`, opacity: 1 - ease(frame, at + 38, at + 46) }}>
          <IDoc size={110} color={C.violet} stroke={1.6} />
        </div>
        <div style={{ position: "absolute", right: 0, top: 30, opacity: ease(frame, at + 40, at + 50) }}>
          <Pill color={C.amber} size={24} mono>checkpoint.md</Pill>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: portrait ? "column" : "row", gap: 20 }}>
        <Pill color={C.green} size={28} style={{ opacity: ease(frame, gi, gi + 10) }}>
          <ILock size={28} color={C.green} /> .gitignore · private ✓
        </Pill>
        <Pill color={C.cyan} size={28} style={{ opacity: ease(frame, git, git + 10) }}>
          <IBranch size={28} color={C.cyan} /> git state captured
        </Pill>
      </div>
    </AbsoluteFill>
  );
};

const StepScan: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const { word, variant, portrait } = useScene();
  const rejectAt = variant === "long" ? first(word("rejected"), at + 140) : Infinity;
  const fixedAt = isFinite(rejectAt) ? rejectAt + 40 : at + 60;
  const sweep = ((frame - at) % 50) / 50;
  const rejected = frame >= rejectAt && frame < fixedAt;
  const clean = frame >= fixedAt;
  const tokenRow = 3;
  const tieAt = first(word("ties"), at + 50);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: portrait ? "column" : "row", gap: 50 }}>
      <Glass glow={clean ? C.green : rejected ? C.red : C.pink} style={{ width: 460, height: 400, padding: 30, position: "relative", overflow: "hidden" }}>
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} style={{ display: "flex", gap: 10, marginBottom: 22 }}>
            <div style={{ height: 14, width: 60 + ((i * 37) % 120), borderRadius: 6, background: "#ffffff22" }} />
            {i === tokenRow ? (
              <div style={{ height: 22, marginTop: -4, padding: "0 10px", borderRadius: 6, fontFamily: MONO, fontSize: 18, lineHeight: "22px", color: clean ? C.green : C.red, background: clean ? `${C.green}22` : `${C.red}33`, border: `1.5px solid ${clean ? C.green : C.red}` }}>{clean ? "[removed]" : "sk-••••••••••"}</div>
            ) : (
              <div style={{ height: 14, width: 80 + ((i * 53) % 140), borderRadius: 6, background: "#ffffff14" }} />
            )}
          </div>
        ))}
        {!clean && <div style={{ position: "absolute", left: 0, right: 0, top: sweep * 400, height: 4, background: C.pink, boxShadow: `0 0 30px 8px ${C.pink}88` }} />}
      </Glass>
      <div style={{ display: "flex", flexDirection: "column", gap: 24, alignItems: portrait ? "center" : "flex-start" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <IShield size={90} color={clean ? C.green : rejected ? C.red : C.pink} stroke={1.6} />
          <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 44, color: clean ? C.green : rejected ? C.red : C.text }}>{clean ? "Clean · queued" : rejected ? "Rejected" : "Scanning for secrets"}</div>
        </div>
        <div style={{ fontFamily: FONT, fontSize: 28, color: C.muted, maxWidth: 520 }}>{rejected ? "fix it first, never bypass the scan" : "keys · tokens · credentials"}</div>
        <Pill color={C.cyan} size={26} style={{ opacity: ease(frame, tieAt, tieAt + 10) }} mono>
          tied to this launcher session
        </Pill>
      </div>
    </AbsoluteFill>
  );
};

const StepExit: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const { portrait } = useScene();
  const s = useSpring(at);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <Glass glow={C.green} style={{ width: portrait ? "100%" : 1000, padding: "34px 40px", fontFamily: MONO, fontSize: portrait ? 34 : 38, color: C.text, transform: `scale(${0.9 + s * 0.1})`, opacity: s, lineHeight: 1.6 }}>
        <div style={{ color: C.green }}>{typed("✔ Checkpoint saved.", frame, at + 4, 30)}</div>
        <div>
          {typed("Type ", frame, at + 26, 30)}
          {frame > at + 30 && <span style={{ color: C.amber, fontWeight: 700 }}>{typed("/exit", frame, at + 30, 20)}</span>}
          {frame > at + 40 && typed(" — your provider menu will appear.", frame, at + 40, 40)}
          <Caret frame={frame} color={C.green} />
        </div>
      </Glass>
    </AbsoluteFill>
  );
};
