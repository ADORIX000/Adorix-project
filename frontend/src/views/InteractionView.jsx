import { useState } from 'react';
import AvatarOverlay from '../avatar/AvatarOverlay';
import InteractionHUD from '../components/InteractionHUD';

export default function InteractionView({ adUrl, avatarState: initialAvatarState, isMicActive }) {
  // Local override for testing
  const [testState, setTestState] = useState(null);
  
  const currentState = testState || initialAvatarState;

  return (
    <div className="absolute inset-0 w-full h-full z-20 bg-black overflow-hidden">
      {/* Dim the background ad so the Avatar pops out more */}
      <video 
        className="w-full h-full object-cover brightness-40 transition-all duration-500" 
        src={`/ads/${adUrl}`} 
        autoPlay 
        loop 
        muted 
      />
      
      <AvatarOverlay state={currentState} />
      
      {/* Show the mic HUD only if the system is actively recording user audio */}
      {isMicActive && <InteractionHUD showMic={true} />}

      {/* --- DEBUG/TESTING PANEL --- */}
      <div className="absolute top-20 right-5 z-50 bg-black/80 p-4 rounded-lg border border-white/20 text-white font-mono text-xs flex flex-col gap-2">
        <div className="font-bold border-b border-white/20 pb-2 mb-1">Avatar Test Panel</div>
        <div className="flex flex-wrap gap-1 max-w-[200px]">
          {['WAKEUP', 'IDLE', 'TALKING', 'THINKING', 'SLEEP'].map(s => (
            <button 
              key={s}
              onClick={() => setTestState(s)}
              className={`px-2 py-1 rounded ${currentState === s ? 'bg-green-600' : 'bg-white/10 hover:bg-white/20'}`}
            >
              {s}
            </button>
          ))}
          <button 
            onClick={() => setTestState(null)}
            className="px-2 py-1 rounded bg-red-600/50 hover:bg-red-600 w-full mt-1"
          >
            Reset to Backend
          </button>
        </div>
        <div className="mt-2 opacity-50 text-[10px]">
          Current: {currentState}
        </div>
      </div>
    </div>
  );
}