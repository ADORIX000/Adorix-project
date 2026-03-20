import React, { useState, useEffect } from 'react';

const LoopView = ({ adUrl, onEnded }) => {
  const [layers, setLayers] = useState([]);

  useEffect(() => {
    if (!adUrl) return;
    setLayers(prev => {
      // If the adUrl is the exact same as the top layer, don't create a new layer.
      // We will handle replaying the same video in the onEnded handler.
      if (prev.length > 0 && prev[prev.length - 1].url === adUrl) {
        return prev;
      }
      const next = [...prev, { url: adUrl, id: Date.now() }];
      if (next.length > 2) next.shift(); // Keep max 2 layers
      return next;
    });
  }, [adUrl]);

  if (!adUrl) {
    return (
      <div className="w-screen h-screen bg-black flex items-center justify-center text-white font-mono">
        <div className="p-8 border border-white/20 rounded-xl bg-white/5 backdrop-blur-md">
            ⌛ Syncing with Loop Engine...
        </div>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#000', overflow: 'hidden' }}>
      {layers.map((layer, i) => {
        const isActive = i === layers.length - 1;
        
        return (
          <video
            key={layer.id} 
            src={`/ads/${layer.url}`}
            autoPlay
            muted
            onEnded={(e) => {
              if (isActive && onEnded) onEnded();
              if (isActive) {
                setTimeout(() => {
                  if (e.target.paused) e.target.play().catch(console.error);
                }, 100);
              }
            }}
            onError={() => {
              console.error(`LoopView: Failed to load ad ${layer.url}. Skipping.`);
              if (isActive && onEnded) onEnded();
            }}
            style={{ 
              position: 'absolute',
              top: 0, left: 0,
              width: '100%', height: '100%', objectFit: 'cover',
              opacity: isActive ? 1 : 0,
              transition: 'opacity 0.8s ease-in-out',
              zIndex: isActive ? 10 : 1
            }}
          />
        );
      })}

      {/* Seamless Bottom-Center Identifier for the current playlist item */}
      <div className="absolute bottom-[10%] left-1/2 -translate-x-1/2 px-6 py-2 bg-black/40 backdrop-blur-xl rounded-2xl border border-white/5 opacity-40 shadow-2xl z-50">
        <span className="text-white text-[11px] uppercase tracking-[0.3em] font-black">
           AD LOOP: {adUrl.replace('.mp4', '').replace(/_/g, ' ')}
        </span>
      </div>
    </div>
  );
};

export default LoopView;