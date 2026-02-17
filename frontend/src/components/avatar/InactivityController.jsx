import { useEffect, useRef } from "react";

const BACKEND = "http://127.0.0.1:5050";

// timings (edit these)
const REENGAGE_AFTER_MS = 12000; // 12s no activity → re-engage
const SLEEP_AFTER_MS = 25000;    // 25s no activity → sleep

async function setAvatar(state, subtitle) {
  try {
    await fetch(`${BACKEND}/avatar/state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state, subtitle, showBubble: true }),
    });
  } catch (e) {
    // backend might be off; ignore
  }
}

function speakSoft(text) {
  try {
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1;
    u.pitch = 1;
    u.volume = 0.9;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  } catch {}
}

export default function InactivityController({ isAwake }) {
  const lastActiveRef = useRef(Date.now());
  const reengagedRef = useRef(false);

  // call this whenever user interacts
  const markActive = () => {
    lastActiveRef.current = Date.now();
    reengagedRef.current = false;
  };

  useEffect(() => {
    // Track activity: mouse, touch, key, scroll
    const events = ["mousemove", "mousedown", "keydown", "touchstart", "scroll"];
    events.forEach((ev) => window.addEventListener(ev, markActive, { passive: true }));

    const timer = setInterval(async () => {
      if (!isAwake) return; // only re-engage when awake

      const idle = Date.now() - lastActiveRef.current;

      // 1) re-engage
      if (idle > REENGAGE_AFTER_MS && !reengagedRef.current) {
        reengagedRef.current = true;
        await setAvatar("REENGAGE", "👀 Still here? Type your question.");

        // optional soft voice
        // speakSoft("Still there? You can ask me a question.");
      }

      // 2) sleep
      if (idle > SLEEP_AFTER_MS) {
        await setAvatar("SLEEP", "…sleeping (type “wake up”)");
        reengagedRef.current = false;
        lastActiveRef.current = Date.now(); // avoid repeating
      }
    }, 800);

    return () => {
      clearInterval(timer);
      events.forEach((ev) => window.removeEventListener(ev, markActive));
    };
  }, [isAwake]);

  return null; // no UI, only logic
}
