import React from 'react';
import AvatarOverlay from '../avatar/AvatarOverlay';
import { Mic } from 'lucide-react';
import { AVATAR_STATES } from '../avatar/avatarStates';

export default function InteractionView({ adUrl, avatarState, setAvatarState, subtitle, productData, showListing }) {
  // Determine if the AI is actively listening to the user
  // (If she is IDLE, it means she is waiting for the user to speak)
  const isListening = avatarState === AVATAR_STATES.IDLE;

  return (
    <div className="absolute inset-0 w-full h-full z-30 bg-black flex flex-col justify-end">
      
      {/* ========================================== */}
      {/* 1. THE CINEMATIC BACKGROUND (Dimmed Ad) */}
      {/* ========================================== */}
      {adUrl && (
        <video 
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
      <div className={`absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center z-40 transition-opacity duration-500 ${isListening ? 'opacity-100' : 'opacity-0'}`}>
        <div className="w-20 h-20 bg-adorix-blue/20 rounded-full flex items-center justify-center animate-pulse shadow-[0_0_50px_rgba(0,184,255,0.4)] border border-adorix-blue/50">
           <Mic className="text-adorix-blue" size={36} />
        </div>
        <p className="text-adorix-blue font-bold mt-6 tracking-[0.3em] text-sm uppercase animate-pulse">
           Listening...
        </p>
      </div>

      {/* ========================================== */}
      {/* 3. PRODUCT LISTING CARD (Left Side) */}
      {/* ========================================== */}
      {showListing && productData && productData.product_name && (
        <div className="absolute left-12 top-1/2 -translate-y-1/2 w-80 z-40 animate-in fade-in slide-in-from-left duration-1000">
           <div className="bg-black/40 backdrop-blur-2xl p-8 rounded-[2rem] border border-white/10 shadow-2xl relative overflow-hidden group">
              {/* Decorative Glow */}
              <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/20 transition-all duration-500" />
              
              <h3 className="text-blue-400 text-xs font-black tracking-widest uppercase mb-2">Featured Product</h3>
              <h2 className="text-white text-3xl font-bold mb-1 leading-tight">{productData.product_name}</h2>
              {productData.brand && <p className="text-white/60 text-sm mb-6">{productData.brand}</p>}
              
              <div className="space-y-4 mb-8">
                {productData.price && (
                  <div className="flex flex-col">
                    <span className="text-white/40 text-[10px] uppercase font-bold tracking-tighter">Starting At</span>
                    <span className="text-white text-2xl font-black">{productData.price}</span>
                  </div>
                )}
                
                {productData.key_features && productData.key_features.length > 0 && (
                  <div className="pt-4 border-t border-white/5">
                    <ul className="space-y-2">
                      {productData.key_features.slice(0, 3).map((feature, i) => (
                        <li key={i} className="flex items-start gap-2 text-white/80 text-xs leading-relaxed">
                          <span className="text-blue-500 mt-1">✦</span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="bg-blue-600/10 border border-blue-500/20 px-4 py-3 rounded-xl">
                 <p className="text-blue-300 text-[10px] font-bold text-center uppercase tracking-widest">
                    Scan or Ask for Details
                 </p>
              </div>
           </div>
        </div>
      )}

      {/* ========================================== */}
      {/* 4. THE 2D AVATAR OVERLAY */}
      {/* ========================================== */}
      <div className="absolute inset-0 z-50 pointer-events-none">
        <AvatarOverlay avatarState={avatarState} setAvatarState={setAvatarState} />
      </div>

      {/* ========================================== */}
      {/* 5. THE SUBTITLES OVERLAY */}
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