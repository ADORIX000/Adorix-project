import React from 'react';

// Added 'personCount' prop to show how many faces are detected
export default function LiveStatus({ isConnected = true, personCount = 0 }) {
  return (
    // Tailwind: Fixed top-right, flexbox layout, blur effect
    <div className="absolute top-6 right-6 z-50 flex flex-col items-end gap-2">
      
      {/* 1. MAIN BADGE (Connection Status) */}
      <div className={`flex items-center gap-3 px-4 py-2 rounded-full border backdrop-blur-md transition-all duration-300 ${
        isConnected 
          ? 'bg-black/60 border-green-500/30 shadow-[0_0_15px_rgba(34,197,94,0.2)]' 
          : 'bg-red-900/40 border-red-500/30'
      }`}>
        
        {/* Pulsing Dot */}
        <div className="relative flex h-3 w-3">
          {isConnected && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          )}
          <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
        </div>

        {/* Text */}
        <span className="text-white text-xs font-bold tracking-widest">
          {isConnected ? 'SYSTEM LIVE' : 'OFFLINE'}
        </span>
      </div>

      {/* 2. DETECTION BADGE (Only shows when someone is detected) */}
      {isConnected && personCount > 0 && (
        <div className="flex items-center gap-2 px-3 py-1 bg-green-500/20 backdrop-blur-sm rounded-lg border border-green-500/30 animate-in fade-in slide-in-from-top-2 duration-300">
           {/* Icon: Face/Person Symbol */}
           <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-green-400">
             <path fillRule="evenodd" d="M7.5 6a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0ZM3.751 20.105a8.25 8.25 0 0 1 16.498 0 .75.75 0 0 1-.437.695A18.683 18.683 0 0 1 12 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 0 1-.437-.695Z" clipRule="evenodd" />
           </svg>
           
           <span className="text-green-100 text-[10px] font-mono font-bold uppercase">
             {personCount} {personCount === 1 ? 'Person' : 'People'} Detected
           </span>
        </div>
      )}

    </div>
  );
}