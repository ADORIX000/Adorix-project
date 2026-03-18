"use client";

import React, { useState } from 'react';
import State1_Loop from '../../components/views/State1_Loop';

/**
 * TEST PAGE: State1_Loop (formerly LoopView)
 * Access via: http://localhost:3000/test-state1
 */
export default function TestState1Page() {
  const [logs, setLogs] = useState([]);
  const [adUrl, setAdUrl] = useState('10-15_female.mp4');

  const mockOnEnded = () => {
    const logMsg = `[Event] ad_ended triggered at ${new Date().toLocaleTimeString()}`;
    console.log(logMsg);
    setLogs(prev => [logMsg, ...prev].slice(0, 5));
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-white">
      {/* Header / Controls */}
      <div className="p-4 bg-slate-800 border-b border-white/10 flex justify-between items-center z-50">
        <div>
          <h1 className="text-xl font-bold">State 1 (Loop) Test Rig</h1>
          <p className="text-xs text-slate-400">Verifying idle ad rotation and loop signals</p>
        </div>
        
        <div className="flex gap-4">
          <select 
            className="bg-slate-700 px-3 py-1 rounded border border-white/20 text-sm"
            value={adUrl}
            onChange={(e) => setAdUrl(e.target.value)}
          >
            <option value="10-15_female.mp4">10-15 Female</option>
            <option value="50-59_male.mp4">50-59 Male</option>
            <option value="16-29_female.mp4">16-29 Female</option>
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
          <State1_Loop 
            adUrl={adUrl}
            onEnded={mockOnEnded}
          />
        </div>

        {/* Live Logs Overlay */}
        <div className="absolute top-8 right-8 w-80 bg-black/80 backdrop-blur-md p-4 rounded-xl border border-white/10 font-mono text-xs max-h-60 overflow-y-auto pointer-events-none">
          <div className="text-green-400 font-bold mb-2">LIVE STATE 1 LOGS</div>
          {logs.length === 0 && <div className="text-slate-600 italic">Waiting for ad to finish...</div>}
          {logs.map((log, i) => (
            <div key={i} className="mb-1 border-b border-white/5 pb-1 last:border-0">
              {log}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
