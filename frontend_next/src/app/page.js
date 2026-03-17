"use client";

import React, { useState, useEffect } from 'react';
import { useSocket } from '../hooks/useSocket';
import { AVATAR_STATES } from '../components/avatar/avatarStates';
import LoopView from '../components/views/LoopView';
import PersonalizedView from '../components/views/PersonalizedView';
import InteractionView from '../components/views/InteractionView';

export default function App() {
  const [systemId, setSystemId] = useState(1);
  const [activeAd, setActiveAd] = useState('10-15_female.mp4');
  const [avatarState, setAvatarState] = useState(AVATAR_STATES.HIDDEN);
  // Using 127.0.0.1 and direct URL to ensure robust connection in dev
  // Using local proxy /ws to avoid CORS/port issues
  const socketUrl = typeof window !== 'undefined' ? `ws://${window.location.host}/ws` : null;
  const { lastMessage, sendJsonMessage } = useSocket(socketUrl);

  useEffect(() => {
    if (lastMessage) {
      console.log(">>> [WebSocket] Received update:", lastMessage);
      if (lastMessage.system_id) setSystemId(lastMessage.system_id);
      if (lastMessage.ad_url) setActiveAd(lastMessage.ad_url);
      if (lastMessage.avatar_state) setAvatarState(lastMessage.avatar_state);
    }
  }, [lastMessage]);

  return (
    <div className="w-screen h-screen bg-black overflow-hidden relative">
      {/* 1. Dynamic Stage Rendering */}
      {systemId === 1 && (
        <LoopView 
            key="loop"
            adUrl={activeAd} 
            onEnded={() => sendJsonMessage({ type: "NEXT_AD" })} 
        />
      )}
      {systemId === 2 && (
        <PersonalizedView 
            key="personalized"
            systemState={{ ad: activeAd }} 
            isConnected={!!lastMessage} 
            sendJsonMessage={sendJsonMessage}
        />
      )}
      {systemId === 3 && (
        <InteractionView 
          key="interaction"
          adUrl={activeAd} 
          avatarState={avatarState} 
          setAvatarState={setAvatarState} 
        />
      )}

      {/* 2. PRELOADING ENGINE */}
      <div className="hidden opacity-0 pointer-events-none absolute -z-50">
        <video src="/avatar-videos/wakeup.webm" preload="auto" muted />
        <video src="/avatar-videos/listening.webm" preload="auto" muted />
        <video src="/avatar-videos/talking.webm" preload="auto" muted />
      </div>
    </div>
  );
}
