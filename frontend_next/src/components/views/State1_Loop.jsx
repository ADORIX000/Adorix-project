"use client";
import React from 'react';

const State1_Loop = ({ adUrl, onEnded }) => {
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

      {/* Seamless Bottom-Center Identifier for the current playlist item */}
      <div className="absolute bottom-[10%] left-1/2 -translate-x-1/2 px-6 py-2 bg-black/40 backdrop-blur-xl rounded-2xl border border-white/5 opacity-40 shadow-2xl">
        <span className="text-white text-[11px] uppercase tracking-[0.3em] font-black">
           AD LOOP: {adUrl.replace('.mp4', '').replace(/_/g, ' ')}
        </span>
      </div>
    </div>
  );
};

export default State1_Loop;