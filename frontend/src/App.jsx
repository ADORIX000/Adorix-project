import React, { useEffect, useState, useRef } from "react";
import AvatarStage from "./components/avatar/AvatarStage";

export default function App() {
  const [systemState, setSystemState] = useState({
    mode: "LOOP", // LOOP, PERSONALIZED, INTERACTION
    avatar_state: "SLEEP",
    subtitle: "",
    ad: null
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
             setSystemState(prev => ({ ...prev, mode: data.mode, ad: data.ad }));
          } else if (data.action === "AVATAR_STATUS") {
             setSystemState(prev => ({ 
                 ...prev, 
                 avatar_state: data.status, 
                 subtitle: data.subtitle 
             }));
          } else if (data.action === "PLAY_AD") {
              setSystemState(prev => ({ ...prev, ad: data.video }));
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

  // UI Components
  const GreenDot = () => (
    <div style={{
      position: "fixed", top: 20, right: 20, width: 15, height: 15,
      background: "#00ff00", borderRadius: "50%",
      boxShadow: "0 0 10px #00ff00", zIndex: 999
    }} />
  );

  const MicIcon = () => (
    <div style={{
      position: "fixed", bottom: 80, left: "50%", transform: "translateX(-50%)",
      fontSize: 40, color: "white", zIndex: 999
    }}>
      🎙️
    </div>
  );

  const CallToAction = () => (
    <div style={{
      position: "fixed", bottom: 40, left: "50%", transform: "translateX(-50%)",
      color: "white", fontSize: 24, textShadow: "0 2px 4px rgba(0,0,0,0.8)",
      fontFamily: "Arial, sans-serif", zIndex: 999
    }}>
      To interact with Adorix, say <b>"Hey Adorix"</b>
    </div>
  );

  return (
    <div className="kiosk-container" style={{ background: "#070b12", width: "100vw", height: "100vh", overflow: "hidden" }}>
      
      {/* 1. Avatar Layer (Always present but state changes) */}
      <AvatarStage 
        externalState={systemState.avatar_state} 
        externalSubtitle={systemState.subtitle}
      />

      {/* 2. Overlays based on Mode */}
      {systemState.mode !== "LOOP" && <GreenDot />}
      
      {systemState.mode === "PERSONALIZED" && <CallToAction />}
      
      {systemState.avatar_state === "LISTENING" && <MicIcon />}

      {/* 3. Debug Info */}
      <div style={{ position: "fixed", bottom: 10, left: 10, fontSize: 12, opacity: 0.5, color: "white" }}>
        Adorix System | Mode: {systemState.mode} | State: {systemState.avatar_state}
      </div>
    </div>
  );
}