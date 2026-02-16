import React from "react";

export default function LiveStatus({ isConnected }) {
  return (
    <div style={styles.wrap}>
      <span style={{ ...styles.dot, background: isConnected ? "#00ff7f" : "#ff3b30" }} />
      <span style={styles.text}>{isConnected ? "SENSING LIVE" : "DISCONNECTED"}</span>
    </div>
  );
}

const styles = {
  wrap: {
    position: "absolute",
    top: 18,
    left: 18,
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "8px 12px",
    borderRadius: 999,
    background: "rgba(0,0,0,0.35)",
    backdropFilter: "blur(8px)",
    color: "white",
    fontFamily: "system-ui",
    fontWeight: 600,
    letterSpacing: 0.5,
    zIndex: 20,
  },
  dot: { width: 10, height: 10, borderRadius: "50%" },
  text: { fontSize: 12 },
};