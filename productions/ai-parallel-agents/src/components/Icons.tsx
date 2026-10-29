import React from "react";

type P = { size?: number; color?: string; stroke?: number; style?: React.CSSProperties };
const S: React.FC<React.PropsWithChildren<P>> = ({ size = 48, color = "currentColor", stroke = 2, style, children }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" style={style}>
    {children}
  </svg>
);

export const IUser = (p: P) => (<S {...p}><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" /></S>);
export const IDoc = (p: P) => (<S {...p}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h6" /></S>);
export const IFolder = (p: P) => (<S {...p}><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /></S>);
export const IShield = (p: P) => (<S {...p}><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /><path d="M9 12l2 2 4-4" /></S>);
export const IKey = (p: P) => (<S {...p}><circle cx="8" cy="15" r="4" /><path d="M11 12l9-9M17 6l3 3M15 8l2 2" /></S>);
export const ICheck = (p: P) => (<S {...p}><path d="M5 12.5l4.5 4.5L19 7" /></S>);
export const IX = (p: P) => (<S {...p}><path d="M6 6l12 12M18 6L6 18" /></S>);
export const ILock = (p: P) => (<S {...p}><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></S>);
export const IBranch = (p: P) => (<S {...p}><circle cx="6" cy="5" r="2" /><circle cx="6" cy="19" r="2" /><circle cx="18" cy="8" r="2" /><path d="M6 7v10M18 10c0 4-6 3-11 7" /></S>);
export const ISwitch = (p: P) => (<S {...p}><path d="M4 8h13l-3-3M20 16H7l3 3" /></S>);
export const IBolt = (p: P) => (<S {...p}><path d="M13 2L4 14h7l-1 8 9-12h-7z" /></S>);
export const ITarget = (p: P) => (<S {...p}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></S>);
export const ILayers = (p: P) => (<S {...p}><path d="M12 3l9 5-9 5-9-5z" /><path d="M3 13l9 5 9-5" /></S>);
export const IPalette = (p: P) => (<S {...p}><path d="M12 3a9 9 0 1 0 0 18c1.2 0 2-.8 2-2 0-1.4-1-1.7-1-3 0-1.1.9-2 2-2h2a4 4 0 0 0 4-4c0-4-4-7-9-7z" /><circle cx="7.5" cy="11" r="1" /><circle cx="10" cy="7" r="1" /><circle cx="15" cy="7.5" r="1" /></S>);
export const IBrain = (p: P) => (<S {...p}><path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 6 1V5a2 2 0 0 0-3-1zM15 4a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-6 1" /></S>);
export const IRules = (p: P) => (<S {...p}><path d="M4 5h16M4 10h16M4 15h10M4 20h7" /></S>);
export const IList = (p: P) => (<S {...p}><rect x="4" y="4" width="16" height="16" rx="2" /><path d="M8 9l1.5 1.5L12 8M8 15l1.5 1.5L12 14M14 9.5h3M14 15.5h3" /></S>);
export const ICpu = (p: P) => (<S {...p}><rect x="6" y="6" width="12" height="12" rx="2" /><rect x="9.5" y="9.5" width="5" height="5" rx="1" /><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3" /></S>);
export const ITerminal = (p: P) => (<S {...p}><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M7 9l3 3-3 3M13 15h4" /></S>);
export const IEye = (p: P) => (<S {...p}><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></S>);
export const IGauge = (p: P) => (<S {...p}><path d="M4 18a8 8 0 1 1 16 0" /><path d="M12 18l4-6" /></S>);
export const IMail = (p: P) => (<S {...p}><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></S>);
export const IGlobe = (p: P) => (<S {...p}><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c2.5 2.5 3.8 5.5 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.5-3.8-9S9.5 5.5 12 3z" /></S>);
export const IQuestion = (p: P) => (<S {...p}><path d="M9 9a3 3 0 1 1 4 2.8c-.7.3-1 .9-1 1.7V15" /><circle cx="12" cy="19" r=".6" /></S>);
export const IPlay = (p: P) => (<S {...p}><path d="M7 4l13 8-13 8z" /></S>);
export const IRefresh = (p: P) => (<S {...p}><path d="M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5" /></S>);
export const IWarn = (p: P) => (<S {...p}><path d="M12 3l10 18H2z" /><path d="M12 10v5M12 18v.5" /></S>);
