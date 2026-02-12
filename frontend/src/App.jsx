import React, { useEffect, useState } from "react";
import AvatarStage from "./components/avatar/AvatarStage";
import { AVATAR_STATE } from "./components/avatar/avatarStates";

export default function App() {
  const [avatarState, setAvatarState] = useState(AVATAR_STATE.IDLE);
  const [lastMessage, setLastMessage] = useState("");

  useEffect(() => {
    const WS_URL = "ws://localhost:8000/ws";
    const socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      console.log("✅ WebSocket connected");
      setAvatarState(AVATAR_STATE.IDLE);
    };

    socket.onmessage = (event) => {
      console.log("📩 WS message:", event.data);
      setLastMessage(event.data);

      try {
        const data = JSON.parse(event.data);

        if (data.action === "wake") {
          setAvatarState(AVATAR_STATE.LISTENING);
        } 
        else if (data.action === "talk") {
          setAvatarState(AVATAR_STATE.TALKING);
        } 
        else if (data.action === "idle") {
          setAvatarState(AVATAR_STATE.IDLE);
        } 
        else if (
          typeof data.action === "string" &&
          data.action.includes("play")
        ) {
          setAvatarState(AVATAR_STATE.SHOW_AD);
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
    };

    socket.onclose = () => {
      console.log("🔌 WebSocket disconnected");
    };

    return () => socket.close();
  }, []);

  return <AvatarStage state={avatarState} lastMessage={lastMessage} />;
}