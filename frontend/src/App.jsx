import React, { useEffect, useState } from "react";
import AvatarStage from "./components/avatar/AvatarStage";
import { AVATAR_STATE } from "./components/avatar/avatarStates";

export default function App() {
  const [avatarState, setAvatarState] = useState(AVATAR_STATE.IDLE);
  const [lastMessage, setLastMessage] = useState("");
  const [userCount, setUserCount] = useState(0);

  useEffect(() => {
    const WS_URL = "ws://localhost:8000/ws";
    let socket;
    let reconnectTimer;

    const connect = () => {
      socket = new WebSocket(WS_URL);

      socket.onopen = () => {
        console.log("✅ WebSocket connected");
        setAvatarState(AVATAR_STATE.IDLE);
      };

      socket.onmessage = (event) => {
        console.log("📩 WS message:", event.data);
        setLastMessage(event.data);

        try {
          const data = JSON.parse(event.data);

          // Check for ad playback
          if (data.action === "play_ad" || data.ad) {
            setAvatarState(AVATAR_STATE.SHOW_AD);
          } 
          else if (data.action === "wake") {
            setAvatarState(AVATAR_STATE.LISTENING);
          } 
          else if (data.action === "talk") {
            setAvatarState(AVATAR_STATE.TALKING);
          } 
          else if (data.action === "idle") {
            setAvatarState(AVATAR_STATE.IDLE);
          }
          else if (data.users && data.users.count > 0) {
            // Users detected - show detection state
            setUserCount(data.users.count);
            setAvatarState(AVATAR_STATE.LISTENING);
          }
          else {
            setAvatarState(AVATAR_STATE.IDLE);
          }

        } catch {
          // ignore if not valid JSON
        }
      };

      socket.onerror = () => {
        console.log("❌ WebSocket error (backend not running yet)");
        setAvatarState(AVATAR_STATE.ERROR);
        // Try to reconnect
        reconnectTimer = setTimeout(connect, 5000);
      };

      socket.onclose = () => {
        console.log("🔌 WebSocket disconnected, reconnecting in 5s...");
        reconnectTimer = setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      if (socket) socket.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  return <AvatarStage state={avatarState} lastMessage={lastMessage} />;
}