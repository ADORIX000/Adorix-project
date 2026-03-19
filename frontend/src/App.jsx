import React, { useState, useEffect } from 'react';
import { useSocket } from './hooks/useSocket';
import { AVATAR_STATES } from './avatar/avatarStates';
import LoopView from './views/LoopView';
import PersonalizedView from './views/PersonalizedView';
import InteractionView from './views/InteractionView';
import DebugCard from './components/DebugCard';

export default function App() {
  console.log("App: Component Rendering");
  const [systemId, setSystemId] = useState(1);
  const [activeAd, setActiveAd] = useState('10-15_female.mp4');
  const [avatarState, setAvatarState] = useState(AVATAR_STATES.HIDDEN);
  const [subtitle, setSubtitle] = useState("");
  const [offlineIndex, setOfflineIndex] = useState(0);

  // Fallback playlist when backend is offline
  const fallbackAds = [
    '10-15_female.mp4', '10-15_male.mp4', 
    '16-29_female.mp4', '16-29_male.mp4', 
    '30-39_female.mp4', '40-49_female.mp4', '40-49_male.mp4', 
    '50-59_female.mp4', '50-59_male.mp4', 'above-60_female.mp4', 'above-60_male.mp4'
  ];
  
  // Connect directly to the backend on port 8002 to ensure robust WebSocket communication
  const { lastMessage, isConnected, sendJsonMessage } = useSocket('ws://localhost:8002/ws');

  // Sync state seamlessly from backend
  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.system_id) setSystemId(lastMessage.system_id);
      if (lastMessage.ad_url) setActiveAd(lastMessage.ad_url);
      if (lastMessage.avatar_state) setAvatarState(lastMessage.avatar_state);
      if (lastMessage.subtitle !== undefined) setSubtitle(lastMessage.subtitle);
    }
  }, [lastMessage]);

  const handleAdEnded = () => {
    if (isConnected) {
      sendJsonMessage({ type: "AD_ENDED" });
    } else {
      // Offline fallback rotation
      const nextIndex = (offlineIndex + 1) % fallbackAds.length;
      setOfflineIndex(nextIndex);
      setActiveAd(fallbackAds[nextIndex]);
    }
  };

  return (
    <div className="w-screen h-screen bg-black overflow-hidden relative">
      {/* 1. Dynamic Stage Rendering based on State Machine */}
      {systemId === 1 && (
        <LoopView 
            key="loop"
            adUrl={activeAd} 
            onEnded={handleAdEnded} 
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
          subtitle={subtitle}
        />
      )}

      {/* 2. PRELOADING ENGINE (Keeps avatar ready without freezing) */}
      <div className="hidden opacity-0 pointer-events-none absolute -z-50">
        <video src="/avatar-videos/wakeup.webm" preload="auto" muted />
        <video src="/avatar-videos/listening.webm" preload="auto" muted />
        <video src="/avatar-videos/talking.webm" preload="auto" muted />
      </div>

      <DebugCard systemId={systemId} isConnected={isConnected} />

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