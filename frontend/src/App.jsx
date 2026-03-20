import React, { useState, useEffect, useCallback } from 'react';
import useWebSocket from 'react-use-websocket';
import { Mic } from 'lucide-react';

// Sub-component imports for modularity (remain as separate files)
import LoopView from './views/LoopView';
import PersonalizedView from './views/PersonalizedView';
import InteractionView from './views/InteractionView';
import DebugCard from './components/DebugCard';
import { AVATAR_STATES } from './avatar/avatarStates';

const WS_URL = 'ws://127.0.0.1:8002/ws';

export default function App() {
  // 1. STATE MANAGEMENT
  const [systemId, setSystemId] = useState(1);
  const [adUrl, setAdUrl] = useState('20-40_male.mp4');
  const [avatarState, setAvatarState] = useState(AVATAR_STATES.HIDDEN);
  const [subtitle, setSubtitle] = useState('');
  const [productData, setProductData] = useState(null);
  const [showListing, setShowListing] = useState(false);

  // 2. WEBSOCKET INTEGRATION
  const { lastJsonMessage, sendJsonMessage, readyState } = useWebSocket(WS_URL, {
    shouldReconnect: () => true,
    reconnectInterval: 3000,
  });

  const isConnected = readyState === 1;

  // 3. MESSAGE HANDLING
  useEffect(() => {
    if (lastJsonMessage) {
      console.log('App: Received WebSocket message', lastJsonMessage);
      
      // Update state based on incoming payload keys
      if (lastJsonMessage.system_id !== undefined) setSystemId(lastJsonMessage.system_id);
      if (lastJsonMessage.ad_url)                  setAdUrl(lastJsonMessage.ad_url);
      if (lastJsonMessage.avatar_state !== undefined) setAvatarState(lastJsonMessage.avatar_state);
      if (lastJsonMessage.subtitle !== undefined)   setSubtitle(lastJsonMessage.subtitle);
      if (lastJsonMessage.product_data !== undefined) setProductData(lastJsonMessage.product_data);
      if (lastJsonMessage.show_listing !== undefined) setShowListing(lastJsonMessage.show_listing);
    }
  }, [lastJsonMessage]);

  // 4. ACTION HANDLERS
  const handleAdEnded = useCallback(() => {
    console.log('App: Ad ended, notifying backend');
    if (isConnected) {
      sendJsonMessage({ type: 'AD_ENDED' });
    }
  }, [isConnected, sendJsonMessage]);

  const triggerWakeWord = useCallback(() => {
    if (isConnected) {
      sendJsonMessage({ type: 'WAKE_WORD_DETECTED' });
    }
  }, [isConnected, sendJsonMessage]);

  // 5. CONDITIONAL RENDERING (3-STATE MACHINE)
  return (
    <div className="w-screen h-screen bg-black overflow-hidden relative font-sans">
      {/* STATE 1 & 2: Full-screen video player */}
      {(systemId === 1 || systemId === 2) && (
        <div className="absolute inset-0 z-0">
          <LoopView 
            adUrl={adUrl} 
            onEnded={handleAdEnded} 
          />
          
          {/* STATE 2 OVERLAYS: LIVE badge and Mic icon */}
          {systemId === 2 && (
            <div className="absolute inset-0 z-10 pointer-events-none">
              {/* Top Center: LIVE Badge */}
              <div className="absolute top-10 left-1/2 -translate-x-1/2 flex items-center gap-3 bg-red-600/90 px-6 py-2 rounded-full shadow-[0_0_20px_rgba(220,38,38,0.5)] border border-red-400/30">
                <div className="w-3 h-3 bg-white rounded-full animate-pulse" />
                <span className="text-white font-black tracking-widest text-sm uppercase">Personalized Mode</span>
              </div>

              {/* Center/Bottom: Microphone Prompt */}
              <div className="absolute bottom-[20%] left-1/2 -translate-x-1/2 flex flex-col items-center gap-4">
                <div className="bg-black/40 backdrop-blur-xl p-5 rounded-full border border-white/10 shadow-2xl animate-bounce">
                  <Mic className="text-white w-10 h-10" />
                </div>
                <div className="bg-white/10 backdrop-blur-md px-8 py-3 rounded-2xl border border-white/20">
                  <p className="text-white font-bold text-lg tracking-wide">
                    Say <span className="text-blue-400">"Hey Adorix"</span>
                  </p>
                </div>
              </div>

              {/* DEBUG BUTTON: Manually trigger wake word */}
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  triggerWakeWord();
                }}
                className="absolute bottom-6 right-6 bg-white/5 hover:bg-white/20 text-white/40 hover:text-white px-4 py-2 rounded-lg border border-white/10 text-[10px] font-bold uppercase transition-all pointer-events-auto"
              >
                Simulate Wake Word
              </button>
            </div>
          )}
        </div>
      )}

      {/* STATE 3: Interaction Mode (Avatar UI & Subtitles) */}
      {systemId === 3 && (
        <div className="absolute inset-0 z-20">
          <InteractionView 
            adUrl={adUrl}
            avatarState={avatarState}
            setAvatarState={setAvatarState}
            subtitle={subtitle}
            productData={productData}
            showListing={showListing}
          />
        </div>
      )}

      {/* OVERLAY ENGINE: Debug HUD (Always stays on top) */}
      <DebugCard systemId={systemId} isConnected={isConnected} />
      
      {/* GLOBAL PRELOADS: Hidden video elements to keep avatar assets in memory */}
      <div className="hidden">
        <video src="/avatar-videos/wakeup.webm" preload="auto" />
        <video src="/avatar-videos/listening.webm" preload="auto" />
        <video src="/avatar-videos/talking.webm" preload="auto" />
      </div>
    </div>
  );
}