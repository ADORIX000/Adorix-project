import React from 'react';
import { AVATAR_STATES } from './avatarStates';

export default function AvatarOverlay({ avatarState, setAvatarState }) {
  
  // 1. THE TRANSITION HANDLER
  // Automatically handles linear animations ending
  const handleVideoEnd = () => {
    if (avatarState === AVATAR_STATES.WAKEUP) {
      // She finished waving -> Auto-switch to listening/breathing
      setAvatarState(AVATAR_STATES.IDLE);
    }
    else if (avatarState === AVATAR_STATES.SLEEP) {
      // She finished sliding down -> Hide completely
      setAvatarState(AVATAR_STATES.HIDDEN);
    }
  };

  if (avatarState === AVATAR_STATES.HIDDEN) return null;

  return (
    <div className="absolute bottom-0 w-full flex justify-center z-50 pointer-events-none">
      <div className="w-[120%] max-w-[800px]">
        
        {/* NON-LOOPING VIDEOS (Trigger handleVideoEnd) */}
        {avatarState === AVATAR_STATES.WAKEUP && (
          <video 
            src="/avatar/wakeup.webm" 
            autoPlay muted playsInline 
            onEnded={handleVideoEnd} 
            className="w-full h-auto drop-shadow-2xl"
          />
        )}

        {avatarState === AVATAR_STATES.SLEEP && (
          <video 
            src="/avatar/sleep.webm" 
            autoPlay muted playsInline 
            onEnded={handleVideoEnd} 
            className="w-full h-auto drop-shadow-2xl"
          />
        )}

        {/* LOOPING VIDEOS (Run infinitely) */}
        {avatarState === AVATAR_STATES.IDLE && (
          <video 
            src="/avatar/idle.webm" 
            autoPlay loop muted playsInline 
            className="w-full h-auto drop-shadow-2xl"
          />
        )}

        {avatarState === AVATAR_STATES.THINKING && (
          <video 
            src="/avatar/thinking.webm" 
            autoPlay loop muted playsInline 
            className="w-full h-auto drop-shadow-2xl"
          />
        )}

        {avatarState === AVATAR_STATES.TALKING && (
          <video 
            src="/avatar/talking.webm" 
            autoPlay loop muted playsInline 
            className="w-full h-auto drop-shadow-2xl"
          />
        )}
        
      </div>
    </div>
  );
}