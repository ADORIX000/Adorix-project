import React from "react";
import AvatarOverlay from "./AvatarOverlay";

export default function AvatarStage({ state, lastMessage }) {
  return (
    <div style={{ position: "relative" }}>
      <AvatarOverlay state={state} />

      {/* Debug panel (you can remove later) */}
      <div style={styles.debug}>
        <div><b>State:</b> {state}</div>
        <div style={{ opacity: 0.7, marginTop: 6 }}>Last WS:</div>
        <pre style={styles.pre}>{lastMessage || "No message yet"}</pre>
      </div>
    </div>
  );
}

const styles = {
  debug: {
    position: "absolute",
    left: 16,
    bottom: 16,
    background: "rgba(0,0,0,0.55)",
    color: "white",
    padding: 12,
    borderRadius: 10,
    width: 360,
    fontSize: 12,
  },
  pre: {
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    margin: 0,
    marginTop: 6,
  },
};