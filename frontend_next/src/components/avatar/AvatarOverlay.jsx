"use client";
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

  if (avatarState === AVATAR_STATES.HIDDEN || avatarState === 'HIDDEN') return null;

  return (
    <div className="absolute inset-0 w-full h-full flex items-center justify-center z-50 pointer-events-none">
      <div className="w-full h-full">
        
        {/* NON-LOOPING VIDEOS (Trigger handleVideoEnd) */}
        {avatarState === AVATAR_STATES.WAKEUP && (
          <video 
            src="/avatar-videos/wakeup.webm" 
            autoPlay muted playsInline 
            onEnded={handleVideoEnd} 
            className="w-full h-full object-cover drop-shadow-2xl"
          />
        )}

        {avatarState === AVATAR_STATES.SLEEP && (
          <video 
            src="/avatar-videos/sleep.webm" 
            autoPlay muted playsInline 
            onEnded={handleVideoEnd} 
            className="w-full h-full object-cover drop-shadow-2xl"
          />
        )}

        {/* LOOPING VIDEOS (Run infinitely) */}
        {avatarState === AVATAR_STATES.IDLE && (
          <video 
            src="/avatar-videos/listening.webm" 
            autoPlay loop muted playsInline 
            className="w-full h-full object-cover drop-shadow-2xl"
          />
        )}

        {avatarState === AVATAR_STATES.THINKING && (
          <video 
            src="/avatar-videos/thinking.webm" 
            autoPlay loop muted playsInline 
            className="w-full h-full object-cover drop-shadow-2xl"
          />
        )}

        {avatarState === AVATAR_STATES.TALKING && (
          <video 
            src="/avatar-videos/talking.webm" 
            autoPlay loop muted playsInline 
            className="w-full h-full object-cover drop-shadow-2xl"
          />
        )}
        
      </div>
    </div>
  );
}