import React, { useEffect, useState } from "react";
import AvatarStage from "./components/avatar/AvatarStage";

export default function App() {
  const [systemState, setSystemState] = useState({
    mode: "IDLE",
    avatar_state: "SLEEP",
    subtitle: ""
  });

  useEffect(() => {
    const WS_URL = "ws://localhost:8000/ws";
    let socket;

    const connectWS = () => {
      socket = new WebSocket(WS_URL);

      socket.onopen = () => console.log("✅ Adorix Backend Connected");
      
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📩 State Update:", data);
          setSystemState(data);
        } catch (err) {
          console.error("Failed to parse WS message", err);
        }
      };

      socket.onclose = () => {
        console.log("🔌 Disconnected. Retrying in 3s...");
        setTimeout(connectWS, 3000);
      };
    };

    connectWS();
    return () => socket?.close();
  }, []);

  return (
    <div className="kiosk-container" style={{ background: "#070b12" }}>
      {/* Show Avatar in both IDLE and INTERACTION modes, control internal state via system_state */}
      <AvatarStage 
        externalState={systemState.avatar_state} 
        externalSubtitle={systemState.subtitle}
      />

      {/* HUD / Status for Debug */}
      <div style={{ position: "fixed", bottom: 10, left: 10, fontSize: 12, opacity: 0.3, color: "white" }}>
        Adorix System | Mode: {systemState.mode} | State: {systemState.avatar_state}
      </div>
    </div>
  );
}