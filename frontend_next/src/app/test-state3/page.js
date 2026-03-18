"use client";

import React, { useState } from 'react';
import State3_Interaction from '../../components/views/State3_Interaction';
import { AVATAR_STATES } from '../../components/avatar/avatarStates';

/**
 * TEST PAGE: State3_Interaction (formerly InteractionView)
 * Access via: http://localhost:3000/test-state3
 */
export default function TestState3Page() {
  const [logs, setLogs] = useState([]);
  const [avatarState, setAvatarState] = useState(AVATAR_STATES.IDLE);
  const [adUrl, setAdUrl] = useState('10-15_female.mp4');

  const updateAvatarState = (state) => {
    const logMsg = `[State Change] Avatar -> ${state} at ${new Date().toLocaleTimeString()}`;
    console.log(logMsg);
    setLogs(prev => [logMsg, ...prev].slice(0, 5));
    setAvatarState(state);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-white">
      {/* Header / Controls */}
      <div className="p-4 bg-slate-800 border-b border-white/10 flex justify-between items-center z-50">
        <div>
          <h1 className="text-xl font-bold">State 3 (Interaction) Test Rig</h1>
          <p className="text-xs text-slate-400">Verifying Avatar Overlay and Blurred Background</p>
        </div>
        
        <div className="flex gap-4">
          <select 
            className="bg-slate-700 px-3 py-1 rounded border border-white/20 text-sm"
            value={avatarState}
            onChange={(e) => updateAvatarState(e.target.value)}
          >
            <option value={AVATAR_STATES.IDLE}>IDLE (Listening)</option>
            <option value={AVATAR_STATES.TALKING}>TALKING</option>
            <option value={AVATAR_STATES.THINKING}>THINKING</option>
          </select>

          <button 
            onClick={() => window.location.reload()}
            className="bg-blue-600 hover:bg-blue-500 px-4 py-1 rounded text-sm font-medium transition-colors"
          >
            Reset Test
          </button>
        </div>
      </div>

      {/* Main View Area (Portrait Simulation) */}
      <div className="flex-1 flex justify-center items-center p-8 overflow-hidden relative">
        <div className="w-[450px] h-[800px] border-8 border-slate-700 rounded-3xl overflow-hidden shadow-2xl relative bg-black">
          <State3_Interaction 
            adUrl={adUrl}
            avatarState={avatarState}
            setAvatarState={updateAvatarState}
          />
        </div>

        {/* Live Logs Overlay */}
        <div className="absolute top-8 right-8 w-80 bg-black/80 backdrop-blur-md p-4 rounded-xl border border-white/10 font-mono text-xs max-h-60 overflow-y-auto pointer-events-none">
          <div className="text-purple-400 font-bold mb-2">LIVE STATE 3 LOGS</div>
          {logs.map((log, i) => (
            <div key={i} className="mb-1 border-b border-white/5 pb-1 last:border-0">
              {log}
            </div>
          ))}
          <div className="mt-4 p-2 bg-white/5 rounded text-[10px] text-slate-400">
            Note: Avatar videos will only show if correctly placed in public/avatar-videos/
          </div>
        </div>
      </div>
    </div>
  );
}
