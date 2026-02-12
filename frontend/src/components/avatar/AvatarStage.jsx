import React from "react";
import { AVATAR_STATE } from "./avatarStates";

export default function AvatarStage({ state, lastMessage }) {
  const getFace = () => {
    switch (state) {
      case AVATAR_STATE.LISTENING:
        return "👂";
      case AVATAR_STATE.TALKING:
        return "🗣️";
      case AVATAR_STATE.SHOW_AD:
        return "📺";
      case AVATAR_STATE.ERROR:
        return "⚠️";
      case AVATAR_STATE.IDLE:
      default:
        return "🙂";
    }
  };

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Arial",
        gap: 10,
      }}
    >
      <div style={{ fontSize: 120 }}>{getFace()}</div>
      <h2>Avatar State: {state}</h2>

      <div style={{ width: "85%", maxWidth: 900 }}>
        <p style={{ opacity: 0.7, marginBottom: 6 }}>Last WS Message:</p>
        <pre
          style={{
            background: "#111",
            color: "#0f0",
            padding: 12,
            borderRadius: 10,
            overflowX: "auto",
            fontSize: 12,
          }}
        >
          {lastMessage || "No message yet"}
        </pre>
      </div>
    </div>
  );
}