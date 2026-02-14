import { useEffect, useRef, useState } from "react";

const BACKEND = "http://127.0.0.1:5050";

function speak(text, onEnd) {
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1;
  u.pitch = 1;
  u.onend = onEnd || null;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

async function setAvatar(state, subtitle) {
  await fetch(`${BACKEND}/avatar/state`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state, subtitle, showBubble: true }),
  });
}

async function askRouter(question) {
  const res = await fetch(`${BACKEND}/router/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const data = await res.json();
  return data.answer || "Sorry, I couldn't find an answer.";
}

export default function VoiceLoop() {
  const [enabled, setEnabled] = useState(false);
  const modeRef = useRef("WAIT_WAKE"); // WAIT_WAKE | WAIT_QUESTION
  const recRef = useRef(null);
  const busyRef = useRef(false); // true while speaking

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      console.warn("SpeechRecognition not supported in this browser.");
      return;
    }

    const rec = new SR();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onresult = async (event) => {
      if (!enabled) return;
      if (busyRef.current) return;

      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      transcript = transcript.trim();
      const lower = transcript.toLowerCase();

      // Only act on FINAL results (prevents repeated triggers)
      const last = event.results[event.results.length - 1];
      const isFinal = last.isFinal;

      if (!isFinal) return;

      // MODE 1: waiting for wake word
      if (modeRef.current === "WAIT_WAKE") {
        if (lower.includes("wake up")) {
          modeRef.current = "WAIT_QUESTION";

          await setAvatar("WAKE", "Hi! I’m awake. Ask your question.");
          busyRef.current = true;

          speak("Hi! I’m awake. What can I help you with?", async () => {
            busyRef.current = false;
            await setAvatar("IDLE", "Listening… Ask your question.");
          });
        }
        return;
      }

      // MODE 2: waiting for question
      if (modeRef.current === "WAIT_QUESTION") {
        const question = transcript;

        await setAvatar("SPEAKING", `You asked: "${question}"`);
        busyRef.current = true;

        const answer = await askRouter(question);

        // Speak answer, then go idle listening again
        speak(answer, async () => {
          busyRef.current = false;
          await setAvatar("IDLE", "Listening… say your next question, or say “sleep”.");
        });

        // Optional: say "sleep" to go back to sleep
        if (lower.includes("sleep")) {
          modeRef.current = "WAIT_WAKE";
          busyRef.current = true;
          await setAvatar("SLEEP", "…sleeping (say “wake up”)");
          speak("Going to sleep. Say wake up when you need me.", () => {
            busyRef.current = false;
          });
        }
      }
    };

    rec.onerror = () => {
      // keep silent; browser might block mic until permission
    };

    rec.onend = () => {
      // auto-restart if enabled
      if (enabled) {
        try { rec.start(); } catch {}
      }
    };

    recRef.current = rec;

    return () => {
      try { rec.stop(); } catch {}
    };
  }, [enabled]);

  const start = async () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      alert("SpeechRecognition not supported. Use Chrome.");
      return;
    }
    modeRef.current = "WAIT_WAKE";
    setEnabled(true);
    await setAvatar("SLEEP", "…sleeping (say “wake up”)");
    try {
      recRef.current?.start();
    } catch {}
  };

  const stop = async () => {
    setEnabled(false);
    try { recRef.current?.stop(); } catch {}
    window.speechSynthesis.cancel();
    await setAvatar("SLEEP", "Voice stopped. Press W or start voice again.");
  };

  return (
    <div style={{ position: "absolute", top: 16, right: 16, display: "flex", gap: 10 }}>
      {!enabled ? (
        <button className="btn" onClick={start}>Start Voice</button>
      ) : (
        <button className="btn" onClick={stop}>Stop Voice</button>
      )}
    </div>
  );
}
