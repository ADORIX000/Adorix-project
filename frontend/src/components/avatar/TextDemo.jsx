import { useState } from "react";

const BACKEND = "http://127.0.0.1:5050";

async function setAvatar(state, subtitle) {
  await fetch(`${BACKEND}/avatar/state`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state, subtitle, showBubble: true }),
  });
}

function speak(text, onEnd) {
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1;
  u.pitch = 1;
  u.onend = onEnd || null;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}

async function askRouter(question) {
  const res = await fetch(`${BACKEND}/router/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const data = await res.json();
  return data.answer || "Sorry, I could not find an answer.";
}

export default function TextDemo({ onAwakeChange }) {
  const [text, setText] = useState("");
  const [awake, setAwake] = useState(false);

  const send = async () => {
    const t = text.trim();
    if (!t) return;

    // Step 1: wake word
    if (!awake && t.toLowerCase().includes("wake up")) {
      setAwake(true);
      onAwakeChange?.(true);
      await setAvatar("WAKE", "Hi! I’m awake. Type your question.");
      speak("Hi! I'm awake. What can I help you with?", async () => {
        await setAvatar("IDLE", "Type your question below.");
      });
      setText("");
      return;
    }

    // Step 2: question
    if (awake) {
      await setAvatar("SPEAKING", `You asked: "${t}"`);
      const answer = await askRouter(t);
      speak(answer, async () => {
        await setAvatar("IDLE", "Type another question, or type 'sleep'.");
      });

      // sleep command
      if (t.toLowerCase().includes("sleep")) {
        setAwake(false);
        onAwakeChange?.(false);
        await setAvatar("SLEEP", "…sleeping (type “wake up”)");
        speak("Going to sleep. Type wake up when you need me.");
      }

      setText("");
      return;
    }

    // If not awake and they typed something else
    await setAvatar("SLEEP", "Type “wake up” to start.");
    setText("");
  };

  return (
    <div style={{ position: "absolute", top: 16, left: 16, display: "flex", gap: 10 }}>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder='Type "wake up" then ask...'
        style={{
          width: 320,
          padding: "10px 12px",
          borderRadius: 12,
          border: "1px solid rgba(255,255,255,0.15)",
          background: "rgba(0,0,0,0.35)",
          color: "white",
          outline: "none",
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") send();
        }}
      />
      <button className="btn" onClick={send}>Send</button>
    </div>
  );
}
