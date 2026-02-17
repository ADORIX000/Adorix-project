import React, { useState, useEffect, useRef } from 'react';
import { useSocket } from './hooks/useSocket';

import LiveStatus from './components/LiveStatus';
import LoopView from './views/LoopView';
import PersonalizedView from './views/PersonalizedView';
import InteractionView from './views/InteractionView';
import BackendSimulator from './testing/BackendSimulator';

export default function App() {
  // Connect to the FastAPI WebSocket server
  const { isConnected, lastMessage } = useSocket('ws://localhost:8000/ws');
  
  // State variables controlled by the Python Backend OR the BackendSimulator
  const [kioskMode, setKioskMode] = useState('INTERACTION'); // Defaulting to INTERACTION for testing
  const [activeAd, setActiveAd] = useState('10-15_female.mp4');
  const [avatarState, setAvatarState] = useState('WAKEUP');
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
        <BackendSimulator 
          currentMode={kioskMode}
          setKioskMode={setKioskMode}
          avatarState={avatarState}
          setAvatarState={setAvatarState}
          isMicActive={isMicActive}
          setIsMicActive={setIsMicActive}
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
          setAvatarState={setAvatarState}
          isMicActive={isMicActive}
          isConnected={isConnected} 
        />
        <BackendSimulator 
          currentMode={kioskMode}
          setKioskMode={setKioskMode}
          avatarState={avatarState}
          setAvatarState={setAvatarState}
          isMicActive={isMicActive}
          setIsMicActive={setIsMicActive}
        />
      </div>
    );
  }

  // Default to LoopView
  return (
    <div className="relative w-full h-full flex flex-col bg-black overflow-hidden font-sans">
      <LiveStatus isConnected={isConnected} />
      <LoopView />
      <BackendSimulator 
          currentMode={kioskMode}
          setKioskMode={setKioskMode}
          avatarState={avatarState}
          setAvatarState={setAvatarState}
          isMicActive={isMicActive}
          setIsMicActive={setIsMicActive}
        />
    </div>
  );
}