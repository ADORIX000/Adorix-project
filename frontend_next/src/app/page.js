"use client";

import React, { useState, useEffect } from 'react';
import { useSocket } from '../hooks/useSocket';
import { AVATAR_STATES } from '../components/avatar/avatarStates';
import State1_Loop from '../components/views/State1_Loop';
import State2_Personalized from '../components/views/State2_Personalized';
import State3_Interaction from '../components/views/State3_Interaction';

export default function App() {
  const [systemId, setSystemId] = useState(1);
  const [activeAd, setActiveAd] = useState('10-15_female.mp4');
  const [avatarState, setAvatarState] = useState(AVATAR_STATES.HIDDEN);
  
  // Connect directly to the backend on port 8002 to ensure robust WebSocket communication
  const socketUrl = typeof window !== 'undefined' ? `ws://localhost:8002/ws` : null;
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
        <State1_Loop 
            key="loop"
            adUrl={activeAd} 
            onEnded={() => sendJsonMessage({ type: "AD_ENDED" })} 
        />
      )}
      {systemId === 2 && (
        <State2_Personalized 
            key="personalized"
            systemState={{ ad: activeAd }} 
            isConnected={!!lastMessage} 
            sendJsonMessage={sendJsonMessage}
        />
      )}
      {systemId === 3 && (
        <State3_Interaction 
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
