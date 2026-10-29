import React, { createContext, useContext } from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

export type Word = { w: string; s: number; e: number };
export type Sentence = { text: string; start: number; end: number; words: Word[] };
export type SceneData = { id: string; chapter: string; start: number; end: number; sentences: Sentence[] };
export type VideoData = { id: string; fps: number; duration: number; durationInFrames: number; scenes: SceneData[] };

type Ctx = { scene: SceneData; portrait: boolean; variant: "long" | "short" };
const SceneCtx = createContext<Ctx | null>(null);
export const SceneProvider = SceneCtx.Provider;

export const useScene = () => {
  const ctx = useContext(SceneCtx);
  if (!ctx) throw new Error("useScene outside SceneProvider");
  const { fps } = useVideoConfig();
  const { scene } = ctx;
  const toFrame = (t: number) => Math.round((t - scene.start) * fps);
  const norm = (w: string) => w.toLowerCase().replace(/[^a-z0-9$/-]/g, "");
  /** Frame (relative to scene start) when the nth sentence starts; Infinity if absent. */
  const sentence = (i: number) => (scene.sentences[i] ? toFrame(scene.sentences[i].start) : Infinity);
  /** Frame when a word is spoken (case/punctuation-insensitive). Infinity if absent. */
  const word = (w: string, nth = 0, after = -Infinity) => {
    let n = 0;
    for (const s of scene.sentences)
      for (const x of s.words) {
        const f = toFrame(x.s);
        if (f >= after && norm(x.w) === norm(w)) {
          if (n === nth) return f;
          n++;
        }
      }
    return Infinity;
  };
  const length = toFrame(scene.end);
  return { ...ctx, fps, sentence, word, length };
};

/** 0..1 spring progress starting at frame `at`. */
export const useSpring = (at: number, config = { damping: 16, mass: 0.7, stiffness: 120 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!isFinite(at)) return 0;
  return spring({ frame: frame - at, fps, config });
};

export const ease = (frame: number, a: number, b: number, from = 0, to = 1) =>
  !isFinite(a)
    ? from
    : interpolate(frame, [a, b], [from, to], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: Easing.bezier(0.22, 1, 0.36, 1),
      });

/** First finite cue in the list, else fallback. */
export const first = (...xs: number[]) => xs.find((x) => isFinite(x)) ?? Infinity;

export const Ctx = SceneCtx;
export const useSceneCtx = () => useContext(SceneCtx)!;
export const Box: React.FC<React.PropsWithChildren<{ style?: React.CSSProperties }>> = ({ style, children }) => (
  <div style={{ position: "absolute", inset: 0, ...style }}>{children}</div>
);
