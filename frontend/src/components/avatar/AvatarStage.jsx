import { useEffect, useMemo, useRef, useState } from "react";
import Lottie from "lottie-react";

import idleAnim from "../assets/idle.json";
import wakeAnim from "../assets/wake.json";
import speakingAnim from "../assets/speaking.json";

// TEMP placeholders (replace later with real files)
import listeningAnim from "../assets/idle.json";
import exitAnim from "../assets/wake.json";

/* ---------------- AVATAR STATES ---------------- */
const STATES = {
  SLEEP: {
    label: "SLEEP",
    anim: idleAnim,
    loop: true,
    subtitle: "…sleeping",
  },
  IDLE: {
    label: "IDLE",
    anim: idleAnim,
    loop: true,
    subtitle: "Say “Hey Adorix” to begin",
  },
  REENGAGE: {
    label: "REENGAGE",
    anim: idleAnim,
    loop: true,
    subtitle: "👀 Still here?",
  },
  LISTENING: {
    label: "LISTENING",
    anim: listeningAnim,
    loop: true,
    subtitle: "I’m listening…",
  },
  WAKE: {
    label: "WAKE",
    anim: wakeAnim,
    loop: false,
    subtitle: "Hi! I’m awake.",
    autoNext: "LISTENING",
  },
  SPEAKING: {
    label: "SPEAKING",
    anim: speakingAnim,
    loop: true,
    subtitle: "Here’s what I found…",
  },
  EXIT: {
    label: "EXIT",
    anim: exitAnim,
    loop: false,
    subtitle: "Goodbye!",
    autoNext: "SLEEP",
  },
};

export default function AvatarStage({ externalState, externalSubtitle }) {
  /* ---------------- LOCAL STATE ---------------- */
  const [state, setState] = useState("SLEEP");
  const [showBubble, setShowBubble] = useState(true);
  const [subtitleOverride, setSubtitleOverride] = useState("");
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  const lastExternalRef = useRef(null);

  /* ---------------- SYNC FROM APP (VoiceController) ---------------- */
  useEffect(() => {
    if (externalState && externalState !== lastExternalRef.current) {
      lastExternalRef.current = externalState;
      setState(externalState);
    }

    if (externalSubtitle !== undefined) {
      setSubtitleOverride(externalSubtitle);
    }
  }, [externalState, externalSubtitle]);

  const cfg = useMemo(() => STATES[state], [state]);
  const subtitleText = subtitleOverride || cfg.subtitle;

  /* ---------------- AUTO NEXT (WAKE / EXIT) ---------------- */
  const eventListeners = useMemo(() => {
    if (state !== "WAKE" && state !== "EXIT") return [];
    return [
      {
        eventName: "complete",
        callback: () => {
          const next = STATES[state]?.autoNext;
          if (next) setState(next);
        },
      },
    ];
  }, [state]);

  /* ---------------- DEV KEYBOARD (SAFE) ---------------- */
  useEffect(() => {
    const onKeyDown = (e) => {
      const tag = document.activeElement?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;

      const k = e.key.toLowerCase();
      if (k === "s") setState("SLEEP");
      if (k === "i") setState("IDLE");
      if (k === "w") setState("WAKE");
      if (k === "l") setState("LISTENING");
      if (k === "p") setState("SPEAKING");
      if (k === "e") setState("EXIT");
      if (k === "b") setShowBubble((v) => !v);
      if (k === "c") setSubtitleOverride("");
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  /* ---------------- 👁️ EYE-FOLLOW ILLUSION ---------------- */
  useEffect(() => {
    const onMove = (e) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 4;
      const y = (e.clientY / window.innerHeight - 0.5) * 4;
      setTilt({ x, y });
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  return (
    <main className="kiosk">
      <section className="stage">
        {/* HUD */}
        <div className="hud">
          <span className="badge">{cfg.label}</span>
        </div>

        {/* AVATAR + RING */}
        <div className="avatarWrap">
          {/* GLOW RING */}
          <div className={`glowRing ${state.toLowerCase()}`} />

          {/* AVATAR */}
          <div
            className="lottieWrap"
            style={{ transform: `translate(${tilt.x}px, ${tilt.y}px)` }}
          >
            <Lottie
              animationData={cfg.anim}
              loop={cfg.loop}
              autoplay
              eventListeners={eventListeners}
              style={{ width: "100%", height: "100%" }}
            />
          </div>
        </div>

        {/* SPEECH BUBBLE */}
        {showBubble && (
          <div className={`bubble ${state === "REENGAGE" ? "reengage" : ""}`}>
            <p className="subtitle">{subtitleText}</p>
          </div>
        )}

        {/* DEV HINT */}
        <p className="hint">
          Keyboard: S Sleep · I Idle · W Wake · L Listening · P Speaking · E Exit
        </p>
      </section>
    </main>
  );
}
