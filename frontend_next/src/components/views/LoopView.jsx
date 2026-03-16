"use client";
import React from 'react';

const LoopView = ({ adUrl, onEnded }) => {
  if (!adUrl) {
    return (
      <div className="w-screen h-screen bg-black flex items-center justify-center text-white font-mono">
        <div className="p-8 border border-white/20 rounded-xl bg-white/5 backdrop-blur-md">
            ⌛ Syncing with Loop Engine...
        </div>
      </div>
    );
  }

  const fullPath = `/ads/${adUrl}`;

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#000' }}>
      <video
        key={fullPath} 
        src={fullPath}
        autoPlay
        muted
        onEnded={onEnded}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />

      {/* Subtle Bottom-Center Identifier for the current playlist item */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-black/40 backdrop-blur-md rounded-full border border-white/10 opacity-30">
        <span className="text-white text-[10px] uppercase tracking-widest font-bold">
           Playing: {adUrl}
        </span>
      </div>
    </div>
  );
};

export default LoopView;