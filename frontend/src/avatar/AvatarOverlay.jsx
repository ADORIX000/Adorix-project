import React, { useState, useEffect } from 'react';
import { AVATAR_STATES } from './avatarStates';

const AvatarOverlay = ({ state }) => {
  // Local state to keep track of which video to show
  const [avatarState, setAvatarState] = useState(state || 'WAKEUP');

  // Sync internal state with prop from parent (backend signal)
  useEffect(() => {
    if (state) {
      setAvatarState(state);
    }
  }, [state]);

  // Helper to determine which file to play
  // Handles both state keys (e.g. 'IDLE') and direct file values (e.g. 'listening.webm')
  const getAvatarFile = (currentState) => {
    if (AVATAR_STATES[currentState]) return AVATAR_STATES[currentState];
    return currentState; // Fallback if it's already a filename
  };

  const activeFile = getAvatarFile(avatarState);

  // If we wanted a 'HIDDEN' state, we could return null here
  if (avatarState === 'HIDDEN') return null;

  return (
    <div className="avatar-wrapper fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-2xl z-30 pointer-events-none">
      <div className="relative w-full h-full flex justify-center items-end">
        {/* We use a single video tag that updates its src to avoid layout jumps 
            and ensure smoother transitions between states if they share properties. 
            Alternatively, keeping the multi-conditional approach user started with: */}
        
        {activeFile === AVATAR_STATES.WAKEUP && (
          <video className="w-full h-auto drop-shadow-2xl" src="/avatar-videos/wakeup.webm" autoPlay muted playsInline />
        )}
        
        {(activeFile === AVATAR_STATES.IDLE || activeFile === 'listening.webm') && (
          <video className="w-full h-auto drop-shadow-2xl" src="/avatar-videos/listening.webm" autoPlay loop muted playsInline />
        )}

        {activeFile === AVATAR_STATES.TALKING && (
          <video className="w-full h-auto drop-shadow-2xl" src="/avatar-videos/talking.webm" autoPlay loop muted playsInline />
        )}
        
        {activeFile === AVATAR_STATES.THINKING && (
          <video className="w-full h-auto drop-shadow-2xl" src="/avatar-videos/thinking.webm" autoPlay loop muted playsInline />
        )}
        
        {activeFile === AVATAR_STATES.SLEEP && (
          <video className="w-full h-auto drop-shadow-2xl" src="/avatar-videos/sleep.webm" autoPlay loop muted playsInline />
        )}
      </div>
    </div>
  );
};

export default AvatarOverlay;