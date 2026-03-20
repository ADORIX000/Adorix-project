import React from 'react';
import AvatarOverlay from '../avatar/AvatarOverlay';
import { Mic } from 'lucide-react';
import { AVATAR_STATES } from '../avatar/avatarStates';

export default function InteractionView({ adUrl, avatarState, setAvatarState, subtitle }) {
  // Determine if the AI is actively listening to the user
  // (If she is IDLE, it means she is waiting for the user to speak)
  const isListening = avatarState === AVATAR_STATES.IDLE;

  return (
    <div className="absolute inset-0 w-full h-full z-30 bg-black flex flex-col justify-end">
      
      {/* ========================================== */}
      {/* 1. THE CINEMATIC BACKGROUND (Dimmed Ad) */}
      {/* ========================================== */}
      {/* Only render background ad if we actually have a URL — avoids /ads/ 404 on State 3 entry */}
      {adUrl && (
        <video 
          // We continue playing the targeted ad, but we blur and dim it 
          // so the user's focus shifts entirely to the Avatar.
          className="absolute inset-0 w-full h-full object-cover opacity-30 blur-sm transition-all duration-1000 ease-in-out" 
          src={`/ads/${adUrl}`} 
          autoPlay 
          loop 
          muted 
          playsInline
        />
      )}

      {/* A dark gradient from the bottom to make the Avatar pop out clearly */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent z-0 pointer-events-none"></div>

      {/* ========================================== */}
      {/* 2. THE DYNAMIC MICROPHONE HUD */}
      {/* ========================================== */}
      {/* We only show the pulsing microphone when the AI is waiting for user input */}
      <div className={`absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center z-40 transition-opacity duration-500 ${isListening ? 'opacity-100' : 'opacity-0'}`}>
        <div className="w-20 h-20 bg-adorix-blue/20 rounded-full flex items-center justify-center animate-pulse shadow-[0_0_50px_rgba(0,184,255,0.4)] border border-adorix-blue/50">
           <Mic className="text-adorix-blue" size={36} />
        </div>
        <p className="text-adorix-blue font-bold mt-6 tracking-[0.3em] text-sm uppercase animate-pulse">
           Listening...
        </p>
      </div>

      {/* ========================================== */}
      {/* 3. THE 2D AVATAR OVERLAY */}
      {/* ========================================== */}
      {/* We pass the avatarState down so the Avatar overlay knows which preloaded video to play */}
      <div className="absolute inset-0 z-50 pointer-events-none">
        <AvatarOverlay avatarState={avatarState} setAvatarState={setAvatarState} />
      </div>

      {/* ========================================== */}
      {/* 4. THE SUBTITLES OVERLAY */}
      {/* ========================================== */}
      {subtitle && (
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 w-3/4 max-w-4xl z-50 text-center pointer-events-none">
          <div className="bg-black/60 backdrop-blur-md px-8 py-4 rounded-2xl border border-white/10 shadow-2xl inline-block">
            <p className="text-white text-2xl md:text-3xl font-medium tracking-wide leading-relaxed drop-shadow-md">
              {subtitle}
            </p>
          </div>
        </div>
      )}

    </div>
  );
}