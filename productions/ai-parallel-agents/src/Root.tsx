import React from "react";
import { Composition } from "remotion";
import { Video, OUTRO_HOLD } from "./Video";
import { ThumbA, ThumbB, ThumbC, ThumbShort } from "./Thumbnails";
import type { VideoData } from "./timing";
import longData from "./data/long.json";
import shortData from "./data/short.json";

const L = longData as VideoData;
const S = shortData as VideoData;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="LongVideo" component={Video} durationInFrames={L.durationInFrames + OUTRO_HOLD} fps={30} width={1920} height={1080} defaultProps={{ data: L, portrait: false, audio: "audio/long-mix.wav" }} />
    <Composition id="ShortVideo" component={Video} durationInFrames={S.durationInFrames + OUTRO_HOLD} fps={30} width={1080} height={1920} defaultProps={{ data: S, portrait: true, audio: "audio/short-mix.wav" }} />
    <Composition id="ThumbA" component={ThumbA} durationInFrames={1} fps={30} width={1280} height={720} />
    <Composition id="ThumbB" component={ThumbB} durationInFrames={1} fps={30} width={1280} height={720} />
    <Composition id="ThumbC" component={ThumbC} durationInFrames={1} fps={30} width={1280} height={720} />
    <Composition id="ThumbShort" component={ThumbShort} durationInFrames={1} fps={30} width={1080} height={1920} />
  </>
);
