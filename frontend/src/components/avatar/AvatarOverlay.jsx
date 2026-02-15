import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { AVATAR_STATE } from "./avatarStates";

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

  const blinkTimeoutRef = useRef(null);
  const doubleBlinkTimeoutRef = useRef(null);

  // Blink loop
  useEffect(() => {
    const scheduleBlink = () => {
      const next = 2200 + Math.random() * 2200;

      blinkTimeoutRef.current = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 200);

        if (Math.random() < 0.15) {
          doubleBlinkTimeoutRef.current = setTimeout(() => {
            setBlink(true);
            setTimeout(() => setBlink(false), 160);
          }, 240);
        }

        scheduleBlink();
      }, next);
    };

    scheduleBlink();

    return () => {
      clearTimeout(blinkTimeoutRef.current);
      clearTimeout(doubleBlinkTimeoutRef.current);
    };
  }, []);

  // Mouth animation
  useEffect(() => {
    if (state !== AVATAR_STATE.TALKING) {
      setMouthFrame(0);
      return;
    }
    const t = setInterval(() => setMouthFrame((m) => (m + 1) % 3), 95);
    return () => clearInterval(t);
  }, [state]);

  const mouthSrc = useMemo(() => {
    if (mouthFrame === 1) return LAYERS.mouth1;
    if (mouthFrame === 2) return LAYERS.mouth2;
    return LAYERS.mouth0;
  }, [mouthFrame]);

  const stackMotion =
    state === AVATAR_STATE.IDLE
      ? { y: [0, -3, 0] }
      : state === AVATAR_STATE.LISTENING
      ? { scale: [1, 1.01, 1] }
      : state === AVATAR_STATE.TALKING
      ? { y: [0, -1.5, 0] }
      : { y: 0, scale: 1 };

  const stackTransition =
    state === AVATAR_STATE.LISTENING
      ? { repeat: Infinity, duration: 1.1, ease: "easeInOut" }
      : state === AVATAR_STATE.TALKING
      ? { repeat: Infinity, duration: 0.85, ease: "easeInOut" }
      : state === AVATAR_STATE.IDLE
      ? { repeat: Infinity, duration: 2.8, ease: "easeInOut" }
      : { duration: 0.25 };

  const faceMotion =
    state === AVATAR_STATE.IDLE
      ? { rotate: [0, -0.18, 0] }
      : state === AVATAR_STATE.LISTENING
      ? { rotate: [0, -0.25, 0], scale: [1, 1.004, 1] }
      : state === AVATAR_STATE.TALKING
      ? { rotate: [0, 0.18, 0] }
      : { rotate: 0, scale: 1 };

  const faceTransition =
    state === AVATAR_STATE.LISTENING
      ? { repeat: Infinity, duration: 1.1, ease: "easeInOut" }
      : state === AVATAR_STATE.TALKING
      ? { repeat: Infinity, duration: 0.8, ease: "easeInOut" }
      : state === AVATAR_STATE.IDLE
      ? { repeat: Infinity, duration: 3.2, ease: "easeInOut" }
      : { duration: 0.25 };

  return (
    <div style={styles.stage}>
      <div style={styles.ambientGlow} />

      <motion.div style={styles.stack} animate={stackMotion} transition={stackTransition}>
        
        {/* 🔵 Blue oval ring */}
        {state === AVATAR_STATE.LISTENING && (
          <motion.div
            style={styles.ovalRing}
            animate={{
              scale: [1, 1.05, 1],
              opacity: [0.5, 0.9, 0.5],
            }}
            transition={{
              repeat: Infinity,
              duration: 1.1,
              ease: "easeInOut",
            }}
          />
        )}

        {/* ✨ Avatar-shaped glow */}
        {state === AVATAR_STATE.LISTENING && (
          <motion.img
            src={LAYERS.body}
            alt="glow"
            style={styles.glowSilhouette}
            animate={{
              opacity: [0.25, 0.7, 0.25],
              scale: [1.03, 1.07, 1.03],
            }}
            transition={{ repeat: Infinity, duration: 1.0, ease: "easeInOut" }}
          />
        )}

        {/* BODY */}
        <motion.img
          src={LAYERS.body}
          alt="body"
          style={styles.layer}
          animate={{
            y:
              state === AVATAR_STATE.IDLE
                ? [0, -0.6, 0]
                : state === AVATAR_STATE.LISTENING
                ? [0, -0.4, 0]
                : state === AVATAR_STATE.TALKING
                ? [0, -0.5, 0]
                : 0,
          }}
          transition={{
            repeat:
              state === AVATAR_STATE.IDLE ||
              state === AVATAR_STATE.LISTENING ||
              state === AVATAR_STATE.TALKING
                ? Infinity
                : 0,
            duration: 3.0,
            ease: "easeInOut",
          }}
        />

        {/* FACE GROUP */}
        <motion.div style={styles.faceGroup} animate={faceMotion} transition={faceTransition}>
          <img src={LAYERS.head} alt="head" style={styles.layer} />
          <img
            src={blink ? LAYERS.eyesClosed : LAYERS.eyesOpen}
            alt="eyes"
            style={styles.layer}
          />
          <img src={mouthSrc} alt="mouth" style={styles.layer} />
        </motion.div>
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
  ambientGlow: {
    position: "absolute",
    width: 560,
    height: 560,
    borderRadius: "50%",
    background: "radial-gradient(circle, rgba(0,255,180,0.10), rgba(0,0,0,0))",
    filter: "blur(6px)",
    opacity: 0.85,
    pointerEvents: "none",
  },
  stack: {
    position: "relative",
    width: 420,
    height: 420,
  },
  ovalRing: {
    position: "absolute",
    width: 440,
    height: 520,
    borderRadius: "50%",
    border: "3px solid rgba(0, 150, 255, 0.65)",
    boxShadow: "0 0 25px rgba(0, 150, 255, 0.4)",
    pointerEvents: "none",
  },
  glowSilhouette: {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    objectFit: "contain",
    filter: "blur(18px)",
    opacity: 0.55,
    transform: "scale(1.06)",
    pointerEvents: "none",
  },
  faceGroup: {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    transformOrigin: "50% 72%",
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