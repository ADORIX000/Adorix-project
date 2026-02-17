import { useState, useEffect } from 'react';
import { useSocket } from './hooks/useSocket';

import LiveStatus from './components/LiveStatus';
import LoopView from './views/LoopView';
import PersonalizedView from './views/PersonalizedView';
import InteractionView from './views/InteractionView';

export default function App() {
  // Connect to the FastAPI WebSocket server
  const { isConnected, lastMessage } = useSocket('ws://localhost:8000/ws');
  
  // State variables controlled entirely by the Python Backend
  const [kioskMode, setKioskMode] = useState('LOOP'); // LOOP, PERSONALIZED, INTERACTION
  const [activeAd, setActiveAd] = useState('10-15_female.mp4');
  const [avatarState, setAvatarState] = useState('HIDDEN');
  const [isMicActive, setIsMicActive] = useState(false);

  // Process incoming JSON signals from Python
  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'SET_MODE') setKioskMode(lastMessage.mode);
      if (lastMessage.type === 'PLAY_AD') setActiveAd(lastMessage.ad_url);
      if (lastMessage.type === 'AVATAR_SIGNAL') setAvatarState(lastMessage.state);
      if (lastMessage.type === 'MIC_STATUS') setIsMicActive(lastMessage.active);
    }
  }, [lastMessage]);

  // ✅ Normalize ad path
  const adUrl = typeof activeAd === "string" ? activeAd : "10-15_female.mp4";

  // ✅ Master State Machine: route to views
  if (kioskMode === "PERSONALIZED") {
    return (
      <div className="relative w-full h-full flex flex-col bg-black overflow-hidden font-sans">
        <LiveStatus isConnected={isConnected} />
        <PersonalizedView
          adUrl={adUrl}
          isConnected={isConnected}
        />
      </div>
    );
  }

  if (kioskMode === "INTERACTION") {
    return (
      <div className="relative w-full h-full flex flex-col bg-black overflow-hidden font-sans">
        <LiveStatus isConnected={isConnected} />
        <InteractionView 
          adUrl={adUrl} 
          avatarState={avatarState} 
          isMicActive={isMicActive}
          isConnected={isConnected} 
        />
      </div>
    );
  }

  // Default to LoopView
  return (
    <div className="relative w-full h-full flex flex-col bg-black overflow-hidden font-sans">
      <LiveStatus isConnected={isConnected} />
      <LoopView />
    </div>
  );
}