import React, { useState, useEffect } from 'react';
import { useSocket } from './hooks/useSocket';
import { AVATAR_STATES } from './avatar/avatarStates';
import LoopView from './views/LoopView';
import InteractionView from './views/InteractionView';

export default function App() {
  const [systemId, setSystemId] = useState(1);
  const [activeAd, setActiveAd] = useState('10-15_female.mp4');
  const [avatarState, setAvatarState] = useState(AVATAR_STATES.HIDDEN);
  const { lastMessage } = useSocket('ws://localhost:8000/ws');

  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.system_id) setSystemId(lastMessage.system_id);
      if (lastMessage.ad_url) setActiveAd(lastMessage.ad_url);
      if (lastMessage.avatar_state) setAvatarState(lastMessage.avatar_state);
    }
  }, [lastMessage]);

  return (
    <div className="w-screen h-screen bg-black overflow-hidden relative">
      {/* 1. Dynamic Stage Rendering */}
      {systemId === 1 && <LoopView />}
      {systemId === 3 && <InteractionView adUrl={activeAd} avatarState={avatarState} />}

      {/* 2. PRELOADING ENGINE: Forces browser to cache all .webm and .mp4 assets */}
      <div className="hidden opacity-0 pointer-events-none absolute -z-50">
        <video src="/avatar/wakeup.webm" preload="auto" muted />
        <video src="/avatar/idle.webm" preload="auto" muted />
        <video src="/avatar/talking.webm" preload="auto" muted />
        <video src="/ads/10-15_female.mp4" preload="auto" muted />
        {/* Add all other critical ads here to prevent lag */}
      </div>
    </div>
  );
}