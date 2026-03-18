"use client";
import React from "react";
import AdPlayer from "../AdPlayer";
import LiveStatus from "../LiveStatus";

export default function State2_Personalized({ systemState, isConnected, sendJsonMessage }) {
  // Clean up unused state
  React.useEffect(() => {
    // Initialization or reset logic if needed
  }, [systemState.ad]);

  const handleAdEnd = (e) => {
    // Notify the backend that an ad loop has finished.
    // The backend's AdorixStateManager increments its play_count and will 
    // either push a new STATE 2 (replay) or push STATE 1 (return to loop).
    console.log("[Personalized] Ad ended, notifying backend...");
    sendJsonMessage({ type: "AD_ENDED" });
    
    // Explicitly play again locally to keep video rolling smoothly
    // until the backend pushes the state transition to ID 1.
    if (e && e.target) {
        e.target.play().catch(err => console.error("Error playing ad:", err));
    }
  };

  return (
    <div style={styles.wrap}>
      {/* CSS for Pulse Animations */}
      <style>
        {`
          @keyframes pulse-glow {
            0% { transform: translateX(-50%) scale(1); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4); }
            70% { transform: translateX(-50%) scale(1.05); box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); }
            100% { transform: translateX(-50%) scale(1); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
          }
          @keyframes mic-pulse {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
          }
        `}
      </style>

      {/* Renders the ad and triggers the next one in the playlist when finished */}
      <AdPlayer
        src={systemState.ad ? `/ads/${systemState.ad}` : ""}
        show={true}
        onEnded={handleAdEnd}
      />

      {/* Top Center "Live" Badge for Personalized Mode */}
      <div className="absolute top-8 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-black/60 backdrop-blur-md px-6 py-2.5 rounded-full border border-white/20 shadow-2xl">
        <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse shadow-[0_0_12px_#ef4444]"></div>
        <span className="text-white text-sm font-bold tracking-[0.2em] uppercase">
          PERSONALIZED
        </span>
      </div>

      {/* Bottom Center Microphone Prompt */}
      <div className="absolute bottom-[8%] left-1/2 -translate-x-1/2 z-50 flex flex-col items-center gap-3">
        <div 
          className="bg-black/80 p-4 rounded-full border border-white/20 shadow-lg"
          style={{ animation: 'mic-pulse 2s infinite' }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" x2="12" y1="19" y2="22"></line>
          </svg>
        </div>
        <div className="bg-black/60 backdrop-blur-sm px-6 py-2 rounded-full border border-white/10">
          <span className="text-white font-medium tracking-wide">Say <span className="text-blue-400 font-bold">"Hey Adorix"</span></span>
        </div>
      </div>
    </div>
  );
}

const styles = {
  wrap: {
    position: "relative",
    width: "100vw",
    height: "100vh",
    overflow: "hidden",
    background: "#070b12",
  },
  overlay: {
    position: "absolute",
    top: 40,
    right: 40,
    color: "white",
    zIndex: 10,
    textAlign: "right",
  },
  promptBadge: {
    position: "absolute",
    bottom: "10%",
    left: "50%",
    transform: "translateX(-50%)",
    background: "rgba(255, 255, 255, 0.15)",
    backdropFilter: "blur(12px)",
    padding: "14px 32px",
    borderRadius: "50px",
    border: "1px solid rgba(255, 255, 255, 0.25)",
    boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
    animation: "pulse-glow 2s infinite ease-in-out",
    zIndex: 20,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  promptText: {
    color: "white",
    fontSize: "1.3rem",
    fontWeight: "600",
    letterSpacing: "0.5px",
    whiteSpace: "nowrap",
    textShadow: "0 2px 4px rgba(0,0,0,0.5)",
  },
};