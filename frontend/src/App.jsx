import React, { useEffect, useState, useRef, useMemo } from "react";
import LoopView from "./views/LoopView";
import PersonalizedView from "./views/PersonalizedView";
import InteractionView from "./views/InteractionView";

export default function App() {
  // 1. Define your playlist based on your folder filenames
  const playlist = [
    "ads/10-15_female.mp4",
    "ads/10-15_male.mp4",
    "ads/16-29_female.mp4",
    "ads/16-29_male.mp4",
    "ads/30-39_female.mp4",
    "ads/30-39_male.mp4",
    "ads/40-49_female.mp4",
    "ads/40-49_male.mp4",
    "ads/50-59_female.mp4",
    "ads/50-59_male.mp4",
    "ads/above-60_female.mp4",
    "ads/above-60_male.mp4"
  ];

  const [adIndex, setAdIndex] = useState(0);
  const [systemState, setSystemState] = useState({
    mode: "PERSONALIZED",
    avatar_state: "SLEEP",
    subtitle: "",
    ad: playlist[0], // Start with the first ad
  });

  const ws = useRef(null);

  // 2. Function to switch to the next ad
  const playNextAd = () => {
    setAdIndex((prevIndex) => {
      const nextIndex = (prevIndex + 1) % playlist.length;
      setSystemState((prev) => ({ ...prev, ad: playlist[nextIndex] }));
      return nextIndex;
    });
  };

  useEffect(() => {
    const WS_URL = "ws://localhost:8000/ws";
    const connectWS = () => {
      ws.current = new WebSocket(WS_URL);
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.action === "MODE_SWITCH") {
            setSystemState((prev) => ({ ...prev, mode: data.mode, ad: data.ad }));
          }
          // ... rest of your WS logic
        } catch (err) {
          console.error("Failed to parse WS message", err);
        }
      };
    };
    connectWS();
    return () => ws.current?.close();
  }, []);

  const isConnected = useMemo(
    () => !!ws.current && ws.current.readyState === 1,
    [systemState.mode, systemState.ad]
  );

  const adSrc = typeof systemState.ad === "string"
    ? systemState.ad.startsWith("/") ? systemState.ad : `/${systemState.ad}`
    : null;

  if (systemState.mode === "PERSONALIZED") {
    return (
      <PersonalizedView
        systemState={{ ...systemState, ad: adSrc }}
        isConnected={isConnected}
        onAdEnd={playNextAd} // 3. Pass the callback function
      />
    );
  }

  // ... rest of your route logic
  return <LoopView systemState={systemState} isConnected={isConnected} />;
}