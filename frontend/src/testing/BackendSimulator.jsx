import React, { useState } from 'react';
import { AVATAR_STATES } from '../avatar/avatarStates';

export default function BackendSimulator({ 
  currentMode, 
  setKioskMode, 
  avatarState, 
  setAvatarState, 
  isMicActive, 
  setIsMicActive 
}) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className={`fixed bottom-4 right-4 z-[9999] transition-all duration-300 ${isVisible ? 'w-64' : 'w-12 h-12'}`}>
      {/* Toggle Button */}
      {!isVisible && (
        <button 
          onClick={() => setIsVisible(true)}
          className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg hover:bg-red-700 hover:scale-110 transition-all"
          title="Open Backend Simulator"
        >
          🛠️
        </button>
      )}

      {/* Control Panel */}
      {isVisible && (
        <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-2xl p-4 text-xs font-mono text-white">
          <div className="flex justify-between items-center mb-3 border-b border-gray-700 pb-2">
            <h3 className="font-bold text-green-400">Backend Simulator</h3>
            <button 
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-white"
            >
              ❎
            </button>
          </div>

          {/* Mode Switcher */}
          <div className="mb-4">
            <p className="text-gray-400 mb-1">KIOSK MODE:</p>
            <div className="grid grid-cols-3 gap-1">
              {['LOOP', 'PERSONALIZED', 'INTERACTION'].map(mode => (
                <button
                  key={mode}
                  onClick={() => setKioskMode(mode)}
                  className={`py-1 px-1 rounded text-[9px] ${currentMode === mode ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          {/* Avatar State */}
          <div className="mb-4">
            <p className="text-gray-400 mb-1">AVATAR STATE:</p>
            <div className="grid grid-cols-3 gap-1">
              {Object.keys(AVATAR_STATES).concat(['HIDDEN']).map(state => (
                <button
                  key={state}
                  onClick={() => setAvatarState(AVATAR_STATES[state] || 'HIDDEN')}
                  className={`py-1 px-1 rounded text-[9px] truncate ${avatarState === (AVATAR_STATES[state] || 'HIDDEN') ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                  {state}
                </button>
              ))}
            </div>
          </div>

          {/* Mic Toggle */}
          <div className="mb-2">
            <p className="text-gray-400 mb-1">SENSORS:</p>
            <button
              onClick={() => setIsMicActive(!isMicActive)}
              className={`w-full py-1 rounded ${isMicActive ? 'bg-red-600 animate-pulse' : 'bg-gray-800'}`}
            >
              Mic: {isMicActive ? 'ON 🎤' : 'OFF 🔇'}
            </button>
          </div>

          <div className="mt-2 text-[9px] text-gray-500 text-center">
            Adorix DevTools v1.0
          </div>
        </div>
      )}
    </div>
  );
}
