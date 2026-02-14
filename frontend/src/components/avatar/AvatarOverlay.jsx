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

  // ✅ Blink loop (random-ish + visible)
  useEffect(() => {
    const scheduleBlink = () => {
      const next = 2200 + Math.random() * 2200; // 2.2s - 4.4s
      blinkTimeoutRef.current = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 220);
        scheduleBlink();
      }, next);
    };
    scheduleBlink();
    return () => clearTimeout(blinkTimeoutRef.current);
  }, []);
  // 15% chance of a quick double blink
if (Math.random() < 0.15) {
    setTimeout(() => {
      setBlink(true);
      setTimeout(() => setBlink(false), 180);
    }, 260);
  }

  // ✅ Mouth animation only while TALKING
  useEffect(() => {
    if (state !== AVATAR_STATE.TALKING) {
      setMouthFrame(0);
      return;
    }
    const t = setInterval(() => setMouthFrame((m) => (m + 1) % 3), 110);
    return () => clearInterval(t);
  }, [state]);

  const mouthSrc = useMemo(() => {
    if (mouthFrame === 1) return LAYERS.mouth1;
    if (mouthFrame === 2) return LAYERS.mouth2;
    return LAYERS.mouth0;
  }, [mouthFrame]);

  // ✅ Whole avatar subtle motion (body+face together)
  const stackMotion =
    state === AVATAR_STATE.IDLE
      ? { y: [0, -5, 0], rotate: [0, 0.5, 0] }
      : state === AVATAR_STATE.LISTENING
      ? { scale: [1, 1.02, 1] }
      : state === AVATAR_STATE.TALKING
      ? { y: [0, -2, 0] }
      : { y: 0, rotate: 0, scale: 1 };

  const stackTransition =
    state === AVATAR_STATE.LISTENING
      ? { repeat: Infinity, duration: 1.0, ease: "easeInOut" }
      : state === AVATAR_STATE.TALKING
      ? { repeat: Infinity, duration: 0.8, ease: "easeInOut" }
      : state === AVATAR_STATE.IDLE
      ? { repeat: Infinity, duration: 2.2, ease: "easeInOut" }
      : { duration: 0.25 };

  // ✅ FaceGroup motion (HEAD+EYES+MOUTH together)
  const faceMotion =
    state === AVATAR_STATE.IDLE
      ? { rotate: [0, -0.7, 0], y: [0, -1, 0] }
      : state === AVATAR_STATE.LISTENING
      ? { rotate: [0, -1.2, 0], scale: [1, 1.01, 1] }
      : state === AVATAR_STATE.TALKING
      ? { rotate: [0, 0.6, 0], y: [0, -1.5, 0] }
      : { rotate: 0, y: 0, scale: 1 };

  const faceTransition =
    state === AVATAR_STATE.LISTENING
      ? { repeat: Infinity, duration: 0.9, ease: "easeInOut" }
      : state === AVATAR_STATE.TALKING
      ? { repeat: Infinity, duration: 0.65, ease: "easeInOut" }
      : state === AVATAR_STATE.IDLE
      ? { repeat: Infinity, duration: 2.6, ease: "easeInOut" }
      : { duration: 0.25 };

  return (
    <div style={styles.stage}>
      {/* Listening ring (CSS, no PNG needed) */}
      {state === AVATAR_STATE.LISTENING && (
        <motion.div
          style={styles.ringCss}
          animate={{ scale: [1, 1.08, 1], opacity: [0.45, 1, 0.45] }}
          transition={{ repeat: Infinity, duration: 1.05, ease: "easeInOut" }}
        />
      )}

      <div style={styles.ambientGlow} />

      <motion.div style={styles.stack} animate={stackMotion} transition={stackTransition}>
        {/* BODY */}
        <img src={LAYERS.body} alt="body" style={styles.layer} />

        {/* ✅ FACE GROUP: head + eyes + mouth move together */}
        <motion.div
          style={styles.faceGroup}
          animate={faceMotion}
          transition={faceTransition}
          // makes rotation feel like it's from neck area
          style={{ ...styles.faceGroup, transformOrigin: "50% 65%" }}
        >
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
    background: "radial-gradient(circle, rgba(0,255,180,0.13), rgba(0,0,0,0))",
    filter: "blur(6px)",
    opacity: 0.85,
    pointerEvents: "none",
  },
  ringCss: {
    position: "absolute",
    width: 560,
    height: 560,
    borderRadius: "50%",
    border: "5px solid rgba(0, 255, 180, 0.65)",
    boxShadow: "0 0 45px rgba(0, 255, 180, 0.35)",
    pointerEvents: "none",
  },
  stack: {
    position: "relative",
    width: 420,
    height: 420,
  },
  faceGroup: {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
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