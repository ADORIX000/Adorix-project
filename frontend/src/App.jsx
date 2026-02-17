import React, { useEffect, useState, useRef, useMemo } from "react";

// ✅ Views (leader requirement)
import LoopView from "./views/LoopView";
import PersonalizedView from "./views/PersonalizedView";
import InteractionView from "./views/InteractionView";

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

  const isConnected = useMemo(
    () => !!ws.current && ws.current.readyState === 1,
    [systemState.mode, systemState.avatar_state, systemState.ad]
  );

  // ✅ Normalize ad path
  const adSrc =
    typeof systemState.ad === "string"
      ? systemState.ad.startsWith("/")
        ? systemState.ad
        : `/${systemState.ad}`
      : null;

  // ✅ Master State Machine: route to views
  if (systemState.mode === "PERSONALIZED") {
    return (
      <PersonalizedView
        systemState={{ ...systemState, ad: adSrc }}
        isConnected={isConnected}
      />
    );
  }

  if (systemState.mode === "INTERACTION") {
    return <InteractionView systemState={systemState} isConnected={isConnected} />;
  }

  return <LoopView systemState={systemState} isConnected={isConnected} />;
}