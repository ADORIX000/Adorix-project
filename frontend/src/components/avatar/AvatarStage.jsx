import React, { useState, useEffect } from "react";
import { AVATAR_STATE } from "./avatarStates";

export default function AvatarStage({ state, lastMessage }) {
  const [adData, setAdData] = useState(null);
  const [userData, setUserData] = useState(null);

  useEffect(() => {
    try {
      if (lastMessage && typeof lastMessage === "string") {
        const data = JSON.parse(lastMessage);
        if (data.ad) {
          setAdData(data.ad);
        }
        if (data.users) {
          setUserData(data.users);
        }
      }
    } catch (e) {
      // ignore invalid JSON
    }
  }, [lastMessage]);

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

  // Show full-screen ad when available
  if (adData && state === AVATAR_STATE.SHOW_AD) {
    return (
      <div
        style={{
          height: "100vh",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          background: "#000",
          color: "#fff",
        }}
      >
        <h1 style={{ marginBottom: 20, fontSize: 32 }}>📺 Current Ad</h1>
        <p style={{ fontSize: 18, marginBottom: 20 }}>{adData}</p>
        
        <div
          style={{
            background: "#333",
            padding: 20,
            borderRadius: 10,
            textAlign: "center",
            marginTop: 20,
          }}
        >
          <p>📺 Ad Player: {adData}</p>
          <p style={{ fontSize: 12, opacity: 0.7 }}>
            Check the camera/kiosk window for video playback
          </p>
        </div>
      </div>
    );
  }

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
        background: state === AVATAR_STATE.ERROR ? "#fee" : "#fff",
      }}
    >
      <div style={{ fontSize: 120 }}>{getFace()}</div>
      <h2>Avatar State: {state}</h2>

      {userData && userData.count > 0 && (
        <div
          style={{
            background: "#e8f5e9",
            padding: 20,
            borderRadius: 10,
            textAlign: "center",
            marginTop: 20,
          }}
        >
          <h3>👥 Detected Users: {userData.count}</h3>
          {userData.primary && (
            <p>
              Primary: {userData.primary.gender} - Age {userData.primary.age}
            </p>
          )}
        </div>
      )}

      <div style={{ width: "85%", maxWidth: 900, marginTop: 20 }}>
        <p style={{ opacity: 0.7, marginBottom: 6 }}>Last WS Message:</p>
        <pre
          style={{
            background: "#111",
            color: "#0f0",
            padding: 12,
            borderRadius: 10,
            overflowX: "auto",
            fontSize: 12,
            maxHeight: 150,
          }}
        >
          {lastMessage || "Waiting for messages..."}
        </pre>
      </div>
    </div>
  );
}