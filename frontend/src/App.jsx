import React, { useEffect, useState, useRef } from "react";
import AvatarStage from "./components/avatar/AvatarStage";

// ✅ Use the components you created (matches leader’s folder plan)
import LiveStatus from "./components/LiveStatus";
import InteractionHUD from "./components/InteractionHUD";
import AdPlayer from "./components/AdPlayer";

export default function App() {
  const [systemState, setSystemState] = useState({
    mode: "LOOP", // LOOP, PERSONALIZED, INTERACTION
    avatar_state: "SLEEP",
    subtitle: "",
    ad: null,
  });

  const ws = useRef(null);

  useEffect(() => {
    const WS_URL = "ws://localhost:8000/ws";

    const connectWS = () => {
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => console.log("✅ Adorix Backend Connected");

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.action === "MODE_SWITCH") {
            setSystemState((prev) => ({ ...prev, mode: data.mode, ad: data.ad }));
          } else if (data.action === "AVATAR_STATUS") {
            setSystemState((prev) => ({
              ...prev,
              avatar_state: data.status,
              subtitle: data.subtitle,
            }));
          } else if (data.action === "PLAY_AD") {
            setSystemState((prev) => ({ ...prev, ad: data.video }));
          }
        } catch (err) {
          console.error("Failed to parse WS message", err);
        }
      };

      ws.current.onclose = () => {
        console.log("🔌 Disconnected. Retrying in 3s...");
        setTimeout(connectWS, 3000);
      };
    };

    connectWS();
    return () => ws.current?.close();
  }, []);

  // ✅ Simple boolean for LiveStatus
  const isConnected = !!ws.current && ws.current.readyState === 1;

  // ✅ For AdPlayer (Personalized mode)
  // supports "/ads/xxx.mp4" or "ads/xxx.mp4"
  const adSrc =
    typeof systemState.ad === "string"
      ? systemState.ad.startsWith("/") ? systemState.ad : `/${systemState.ad}`
      : null;

  return (
    <div
      className="kiosk-container"
      style={{
        background: "#070b12",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* ✅ Background video only in PERSONALIZED mode */}
      {systemState.mode === "PERSONALIZED" && adSrc && (
        <AdPlayer src={adSrc} show />
      )}

      {/* ✅ Live status (replaces GreenDot) */}
      {systemState.mode !== "LOOP" && <LiveStatus isConnected={isConnected} />}

      {/* ✅ Avatar Layer (Always present) */}
      <AvatarStage
        externalState={systemState.avatar_state}
        externalSubtitle={systemState.subtitle}
      />

      {/* ✅ HUD (replaces MicIcon + CallToAction)
          - shows Listening/Speaking/Idle based on avatar_state
          - only show HUD in interaction-related modes
      */}
      {systemState.mode !== "LOOP" && (
        <InteractionHUD state={systemState.avatar_state} />
      )}

      {/* Debug Info (keep for now) */}
      <div
        style={{
          position: "fixed",
          bottom: 10,
          left: 10,
          fontSize: 12,
          opacity: 0.5,
          color: "white",
          zIndex: 999,
        }}
      >
        Adorix System | Mode: {systemState.mode} | State: {systemState.avatar_state}
      </div>
    </div>
  );
}