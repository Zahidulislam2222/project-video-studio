import React, { useMemo } from "react";
import { ThreeCanvas } from "@remotion/three";
import { useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";

/** Real WebGL 3D: a wireframe core with an inner glow, orbit rings and a particle shell. */
export const Orb3D: React.FC<{ size: number; color?: string; color2?: string; spin?: number; pulse?: number; style?: React.CSSProperties }> = ({ size, color = "#38BDF8", color2 = "#8B5CF6", spin = 1, pulse = 0, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = (frame / fps) * spin;
  const points = useMemo(() => {
    const n = 420;
    const arr = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const phi = Math.acos(1 - (2 * (i + 0.5)) / n);
      const th = Math.PI * (1 + Math.sqrt(5)) * i;
      const r = 2.25 + ((i * 7919) % 100) / 400;
      arr[i * 3] = r * Math.cos(th) * Math.sin(phi);
      arr[i * 3 + 1] = r * Math.sin(th) * Math.sin(phi);
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(arr, 3));
    return g;
  }, []);
  const s = 1 + pulse * 0.08 * Math.sin(t * 6);
  return (
    <div style={{ width: size, height: size, ...style }}>
      <ThreeCanvas width={size} height={size} camera={{ position: [0, 0, 7], fov: 50 }} gl={{ antialias: true, alpha: true }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[4, 4, 6]} intensity={60} color={color} />
        <pointLight position={[-5, -3, 4]} intensity={40} color={color2} />
        <group rotation={[t * 0.35, t * 0.5, 0]} scale={[s, s, s]}>
          <mesh>
            <icosahedronGeometry args={[1.35, 1]} />
            <meshStandardMaterial color={color} wireframe />
          </mesh>
          <mesh>
            <icosahedronGeometry args={[0.95, 2]} />
            <meshStandardMaterial color={color2} emissive={color2} emissiveIntensity={0.55} roughness={0.25} metalness={0.4} flatShading />
          </mesh>
        </group>
        <group rotation={[1.1, t * 0.8, 0.3]}>
          <mesh>
            <torusGeometry args={[1.9, 0.018, 8, 120]} />
            <meshBasicMaterial color={color} />
          </mesh>
        </group>
        <group rotation={[0.4, -t * 0.6, 1.2]}>
          <mesh>
            <torusGeometry args={[2.1, 0.012, 8, 120]} />
            <meshBasicMaterial color={color2} />
          </mesh>
        </group>
        <points geometry={points} rotation={[0, -t * 0.25, t * 0.1]}>
          <pointsMaterial size={0.035} color={"#CFE8FF"} transparent opacity={0.75} />
        </points>
      </ThreeCanvas>
    </div>
  );
};

/** Floating 3D cubes/shards used as depth accents. */
export const Shards3D: React.FC<{ width: number; height: number; color?: string; count?: number }> = ({ width, height, color = "#38BDF8", count = 9 }) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const items = useMemo(
    () =>
      Array.from({ length: count }).map((_, i) => ({
        x: ((i * 0.618) % 1) * 12 - 6,
        y: ((i * 0.381 + 0.2) % 1) * 7 - 3.5,
        z: -((i * 0.27) % 1) * 6,
        s: 0.18 + ((i * 13) % 7) / 25,
        r: i * 1.3,
      })),
    [count]
  );
  return (
    <ThreeCanvas width={width} height={height} camera={{ position: [0, 0, 8], fov: 50 }} gl={{ alpha: true, antialias: true }}>
      <ambientLight intensity={0.5} />
      <pointLight position={[3, 5, 6]} intensity={50} color={color} />
      <pointLight position={[-6, -2, 3]} intensity={30} color={"#8B5CF6"} />
      {items.map((it, i) => (
        <mesh key={i} position={[it.x, it.y + Math.sin(t * 0.6 + i) * 0.25, it.z]} rotation={[t * 0.4 + it.r, t * 0.3 + it.r, 0]} scale={[it.s, it.s, it.s]}>
          {i % 3 === 0 ? <octahedronGeometry args={[1, 0]} /> : <boxGeometry args={[1, 1, 1]} />}
          <meshStandardMaterial color={i % 2 ? color : "#8B5CF6"} roughness={0.3} metalness={0.6} transparent opacity={0.55} />
        </mesh>
      ))}
    </ThreeCanvas>
  );
};
