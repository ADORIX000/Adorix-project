import React from "react";

export default function InteractionHUD({ state }) {
  const label =
    state === "LISTENING"
      ? "Listening…"
      : state === "TALKING"
      ? "Speaking…"
      : "Idle";

  return (
    <div style={styles.wrap}>
      <div style={styles.mic}>🎤</div>
      <div style={styles.text}>{label}</div>
    </div>
  );
}

const styles = {
  wrap: {
    position: "absolute",
    bottom: 22,
    left: "50%",
    transform: "translateX(-50%)",
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "10px 14px",
    borderRadius: 16,
    background: "rgba(0,0,0,0.35)",
    backdropFilter: "blur(8px)",
    color: "white",
    fontFamily: "system-ui",
    zIndex: 20,
  },
  mic: { fontSize: 18 },
  text: { fontSize: 14, fontWeight: 600 },
};