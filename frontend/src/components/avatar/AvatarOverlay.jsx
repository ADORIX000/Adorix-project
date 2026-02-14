import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { AVATAR_STATE } from "./avatarStates";

// Uses assets from: frontend/public/avatar/
const LAYERS = {
  body: "/avatar/body.png",
  head: "/avatar/head.png",
  eyesOpen: "/avatar/eyes_open.png",
  eyesClosed: "/avatar/eyes_closed.png",
  mouth0: "/avatar/mouth_0.png",
  mouth1: "/avatar/mouth_1.png",
  mouth2: "/avatar/mouth_2.png",
};

export default function AvatarOverlay({ state }) {
  const [blink, setBlink] = useState(false);
  const [mouthFrame, setMouthFrame] = useState(0);

  // --- Blink loop (random-ish) ---
  const blinkTimeoutRef = useRef(null);
  useEffect(() => {
    const scheduleBlink = () => {
      const next = 2200 + Math.random() * 2200; // 2.2s - 4.4s
      blinkTimeoutRef.current = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 220); // visible blink
        scheduleBlink();
      }, next);
    };
    scheduleBlink();
    return () => clearTimeout(blinkTimeoutRef.current);
  }, []);

  // --- Mouth animation only while TALKING ---
  useEffect(() => {
    if (state !== AVATAR_STATE.TALKING) {
      setMouthFrame(0);
      return;
    }
    const t = setInterval(() => {
      setMouthFrame((m) => (m + 1) % 3);
    }, 110);
    return () => clearInterval(t);
  }, [state]);

  const mouthSrc = useMemo(() => {
    if (mouthFrame === 1) return LAYERS.mouth1;
    if (mouthFrame === 2) return LAYERS.mouth2;
    return LAYERS.mouth0;
  }, [mouthFrame]);

  // --- Motion presets per state (pro-feel) ---
  const stackMotion =
    state === AVATAR_STATE.IDLE
      ? {
          y: [0, -5, 0],
          rotate: [0, 0.6, 0],
        }
      : state === AVATAR_STATE.LISTENING
      ? {
          scale: [1, 1.02, 1],
          rotate: [0, -0.9, 0],
        }
      : state === AVATAR_STATE.TALKING
      ? {
          y: [0, -2, 0],
          rotate: [0, 0.4, 0],
        }
      : {
          y: 0,
          rotate: 0,
          scale: 1,
        };

  const stackTransition =
    state === AVATAR_STATE.LISTENING
      ? { repeat: Infinity, duration: 0.95, ease: "easeInOut" }
      : state === AVATAR_STATE.TALKING
      ? { repeat: Infinity, duration: 0.75, ease: "easeInOut" }
      : state === AVATAR_STATE.IDLE
      ? { repeat: Infinity, duration: 2.2, ease: "easeInOut" }
      : { duration: 0.25 };

  return (
    <div style={styles.stage}>
      {/* CSS Listening ring (no PNG needed) */}
      {state === AVATAR_STATE.LISTENING && (
        <motion.div
          style={styles.ringCss}
          animate={{ scale: [1, 1.08, 1], opacity: [0.45, 1, 0.45] }}
          transition={{ repeat: Infinity, duration: 1.05, ease: "easeInOut" }}
        />
      )}

      {/* Extra subtle ambient glow always */}
      <div style={styles.ambientGlow} />

      {/* Whole avatar stack motion */}
      <motion.div style={styles.stack} animate={stackMotion} transition={stackTransition}>
        {/* Body stays stable (feels grounded) */}
        <img src={LAYERS.body} alt="body" style={styles.layer} />

        {/* Head can have a tiny independent micro-motion for realism */}
        <motion.img
          src={LAYERS.head}
          alt="head"
          style={styles.layer}
          animate={
            state === AVATAR_STATE.IDLE
              ? { rotate: [0, -0.4, 0] }
              : state === AVATAR_STATE.TALKING
              ? { rotate: [0, 0.35, 0] }
              : { rotate: 0 }
          }
          transition={{
            repeat: state === AVATAR_STATE.IDLE || state === AVATAR_STATE.TALKING ? Infinity : 0,
            duration: state === AVATAR_STATE.TALKING ? 0.65 : 2.6,
            ease: "easeInOut",
          }}
        />

        {/* Eyes (blink swap) */}
        <img
          src={blink ? LAYERS.eyesClosed : LAYERS.eyesOpen}
          alt="eyes"
          style={styles.layer}
        />

        {/* Mouth (talk frames) */}
        <img src={mouthSrc} alt="mouth" style={styles.layer} />
      </motion.div>
    </div>
  );
}

const styles = {
  stage: {
    height: "100vh",
    display: "grid",
    placeItems: "center",
    background: "radial-gradient(circle at center, #1f1f2e 0%, #0b0b14 70%)",
    overflow: "hidden",
    position: "relative",
  },

  // Subtle glow behind avatar always
  ambientGlow: {
    position: "absolute",
    width: 560,
    height: 560,
    borderRadius: "50%",
    background: "radial-gradient(circle, rgba(0,255,180,0.13), rgba(0,0,0,0))",
    filter: "blur(6px)",
    opacity: 0.8,
    pointerEvents: "none",
  },

  // Listening ring (CSS)
  ringCss: {
    position: "absolute",
    width: 560,
    height: 560,
    borderRadius: "50%",
    border: "5px solid rgba(0, 255, 180, 0.65)",
    boxShadow: "0 0 45px rgba(0, 255, 180, 0.35)",
    pointerEvents: "none",
  },

  // Stack size: adjust for your avatar scale
  stack: {
    position: "relative",
    width: 420,
    height: 420,
  },

  layer: {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    objectFit: "contain",
    pointerEvents: "none",
  },
};