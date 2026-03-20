import React from 'react';

export default function DebugCard({ systemId, isConnected }) {
  const getBackendStatus = () => {
    if (!isConnected) return "Disconnected (OFFLINE)";
    if (systemId === 1) return "_state_loop (Python)";
    if (systemId === 2) return "_state_personalized (Python)";
    if (systemId === 3) return "_state_interaction (RAG/STT)";
    return "Unknown";
  };

  const getFrontendLogic = () => {
    if (!isConnected && systemId === 1) return "Offline Fallback Rotation (React)";
    if (systemId === 1) return "LoopView (WebSocket Syncing)";
    if (systemId === 2) return "PersonalizedView (WebSocket Syncing)";
    if (systemId === 3) return "InteractionView (Cinematic Sync)";
    return "Unknown";
  };

  const getCameraStatus = () => {
    if (!isConnected) return "⚪ Offline";
    if (systemId === 1) return "🟢 Scanning for faces";
    if (systemId === 2) return "🟢 Tracking user presence";
    if (systemId === 3) return "⚪ Standby";
    return "Unknown";
  };

  const getMicStatus = () => {
    if (!isConnected) return "⚪ Offline";
    if (systemId === 1) return "🔴 Muted";
    if (systemId === 2) return "🟢 Listening for 'Wake Word'";
    if (systemId === 3) return "🟢 Listening for Questions";
    return "Unknown";
  };

  const getNextAction = () => {
    if (systemId === 1) return "Step in front of the camera to trigger a Personalized Ad (System ID: 2).";
    if (systemId === 2) return "Wait for 2 loops to finish OR say the wake word to trigger Interaction (System ID: 3).";
    if (systemId === 3) return "Ask a question to hear an answer, OR wait 5 seconds silently to exit to Loop Mode (System ID: 1).";
    return "";
  };

  return (
    <div className="absolute top-4 left-4 z-[9999] bg-black/80 backdrop-blur-md p-5 rounded-xl border border-white/20 text-white font-mono text-xs max-w-[320px] shadow-2xl pointer-events-none">
      <h3 className="text-sm font-bold mb-3 text-[#00b8ff] uppercase tracking-widest border-b border-white/20 pb-2">Diagnostic HUD</h3>
      
      <div className="space-y-4">
        <div className="flex justify-between items-center bg-white/5 p-2 rounded-md">
          <span className="text-gray-300 font-bold uppercase tracking-wider">Live State ID:</span>
          <span className="text-[#22c55e] text-xl font-black">{systemId}</span>
        </div>
        
        <div>
          <span className="text-gray-400 font-bold block uppercase mb-1 border-b border-white/5 pb-1 tracking-wider text-[10px]">Architecture</span>
          <div className="flex flex-col gap-1 mt-2 text-[11px]">
            <span className="text-gray-300">Backend: <span className="text-white font-bold block truncate">{getBackendStatus()}</span></span>
            <span className="text-gray-300">Frontend: <span className="text-white font-bold block truncate">{getFrontendLogic()}</span></span>
          </div>
        </div>

        <div>
          <span className="text-gray-400 font-bold block uppercase mb-1 border-b border-white/5 pb-1 tracking-wider text-[10px]">Hardware Sensing</span>
          <div className="flex flex-col gap-1 mt-2 text-[11px]">
            <span className="text-gray-300">Camera: <span className="text-white font-bold block truncate">{getCameraStatus()}</span></span>
            <span className="text-gray-300">Mic: <span className="text-white font-bold block truncate">{getMicStatus()}</span></span>
          </div>
        </div>

        <div className="bg-[#00b8ff]/10 p-3 rounded-lg border border-[#00b8ff]/30 mt-4">
          <span className="text-[#00b8ff] font-bold block uppercase mb-1 tracking-wider text-[10px]">How to Trigger Next State:</span>
          <span className="text-gray-200 leading-relaxed text-[11px] block mt-1">{getNextAction()}</span>
        </div>
      </div>
    </div>
  );
}
