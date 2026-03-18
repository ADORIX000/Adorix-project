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
  
  // Connect cleanly to the backend via our Next.js reverse proxy (port 8002)
  const socketUrl = typeof window !== 'undefined' ? `ws://${window.location.host}/ws` : null;
  const { lastMessage, sendJsonMessage } = useSocket(socketUrl);

  // Sync state seamlessly from backend
  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.system_id) setSystemId(lastMessage.system_id);
      if (lastMessage.ad_url) setActiveAd(lastMessage.ad_url);
      if (lastMessage.avatar_state) setAvatarState(lastMessage.avatar_state);
    }
  }, [lastMessage]);

  return (
    <div className="w-screen h-screen bg-black overflow-hidden relative">
      {/* 1. Dynamic Stage Rendering based on State Machine */}
      {systemId === 1 && (
        <LoopView 
            key="loop"
            adUrl={activeAd} 
            onEnded={() => sendJsonMessage({ type: "AD_ENDED" })} 
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

      {/* 2. PRELOADING ENGINE (Keeps avatar ready without freezing) */}
      <div className="hidden opacity-0 pointer-events-none absolute -z-50">
        <video src="/avatar-videos/wakeup.webm" preload="auto" muted />
        <video src="/avatar-videos/listening.webm" preload="auto" muted />
        <video src="/avatar-videos/talking.webm" preload="auto" muted />
      </div>
    </div>
  );
}
