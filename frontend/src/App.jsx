import React, { useState, useEffect } from 'react';
import { useSocket } from './hooks/useSocket';
import { AVATAR_STATES } from './avatar/avatarStates';
import LoopView from './views/LoopView';
import PersonalizedView from './views/PersonalizedView';
import InteractionView from './views/InteractionView';

export default function App() {
  console.log("App: Component Rendering");
  const [systemId, setSystemId] = useState(1);
  const [activeAd, setActiveAd] = useState('10-15_female.mp4');
  const [avatarState, setAvatarState] = useState(AVATAR_STATES.HIDDEN);
  
  // Connect directly to the backend on port 8002 to ensure robust WebSocket communication
  const { lastMessage, sendJsonMessage } = useSocket('ws://localhost:8002/ws');

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

      {/* DEBUG BUTTON: Manually trigger wake word in State 2 */}
      {systemId === 2 && (
        <button 
          onClick={() => sendJsonMessage({ type: "WAKE_WORD_DETECTED" })}
          className="absolute bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 text-sm font-bold opacity-50 hover:opacity-100 transition-opacity"
        >
          [DEBUG] Trigger Wake Word
        </button>
      )}
    </div>
  );
}